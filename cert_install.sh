#!/bin/bash
# =============================================================================
# cert_install.sh — Install a new TLS certificate issued by USF IT / InCommon
#
# Usage:
#   bash cert_install.sh              # auto-detects files in certs/incoming/
#   make cert-update                  # same thing via make
#
# Place the files delivered by USF IT in certs/incoming/ before running.
# Expected filenames (delivered as a zip):
#   *_cert.cer       leaf certificate
#   *_interm.cer     InCommon intermediate certificate
#   *.key            private key (PKCS#8 PEM)
#
# The script will:
#   1. Auto-detect the three files above
#   2. Validate the key-cert match and expiry
#   3. Assemble fullchain.pem (leaf + intermediate)
#   4. Back up the current live certs to certs/backup/<timestamp>/
#   5. Install fullchain.pem and privkey.pem
#   6. Reload nginx with zero downtime (never stops the container)
#   7. Verify the live cert via openssl s_client
#   8. Remove certs/incoming/
#
# Safe to re-run: if nginx -t fails the old cert keeps serving; restore from
# the timestamped backup and reload again.
# =============================================================================

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
INCOMING="$REPO_DIR/certs/incoming"
TMPDIR=$(mktemp -d /tmp/cert_install.XXXXXX)
DOMAIN="mbon-dashboards.marine.usf.edu"
LOG_TAG="[cert_install $(date -u '+%Y-%m-%dT%H:%M:%SZ')]"

cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT

log()  { echo "$LOG_TAG $*"; }
die()  { echo "$LOG_TAG ERROR: $*" >&2; exit 1; }

cd "$REPO_DIR"

# ── 0. Locate the incoming files ─────────────────────────────────────────────
log "Looking for cert files in certs/incoming/ ..."

[ -d "$INCOMING" ] || die "certs/incoming/ does not exist. Copy IT-delivered files there first."

CERT=$(ls "$INCOMING"/*_cert.cer 2>/dev/null | head -1)
INTERM=$(ls "$INCOMING"/*_interm.cer 2>/dev/null | head -1)
KEY=$(ls "$INCOMING"/*.key 2>/dev/null | head -1)

[ -n "$CERT"  ] || die "No *_cert.cer found in certs/incoming/"
[ -n "$INTERM" ] || die "No *_interm.cer found in certs/incoming/"
[ -n "$KEY"   ] || die "No *.key found in certs/incoming/"

log "Leaf cert:    $CERT"
log "Intermediate: $INTERM"
log "Private key:  $KEY"

# ── 1. Validate key ↔ cert match ─────────────────────────────────────────────
log "Validating key-cert match..."
CERT_MOD=$(openssl x509 -noout -modulus -in "$CERT" 2>/dev/null | sha256sum | awk '{print $1}')
KEY_MOD=$(openssl rsa   -noout -modulus -in "$KEY"  2>/dev/null | sha256sum | awk '{print $1}')
# NOTE: use 'openssl rsa', not 'openssl pkey', for PKCS#8 PEM keys from InCommon

if [ "$CERT_MOD" != "$KEY_MOD" ]; then
    die "Private key does NOT match the certificate. Aborting before touching anything."
fi
log "✓ Key matches cert."

# ── 2. Check expiry and hostname ─────────────────────────────────────────────
log "Checking cert details..."
openssl x509 -noout -dates -subject -ext subjectAltName -in "$CERT" 2>/dev/null
openssl x509 -noout -checkend 0 -in "$CERT" 2>/dev/null \
    || die "Certificate is already expired. Aborting."
log "✓ Cert is not expired."

# Trust reference for chain validation. Prefer the current Mozilla CA list —
# that is what browsers actually trust. The host's ca-certificates.crt can lag
# or omit roots such as "eSign Root CA - G1", which would make a perfectly
# good chain look broken and abort the install for no reason.
MOZILLA_CA_URL="https://curl.se/ca/cacert.pem"
TRUST_BUNDLE="$TMPDIR/trust.pem"
if curl -fsSL --max-time 25 "$MOZILLA_CA_URL" -o "$TRUST_BUNDLE" 2>/dev/null \
   && [ -s "$TRUST_BUNDLE" ] && grep -q 'BEGIN CERTIFICATE' "$TRUST_BUNDLE"; then
    log "Trust reference: Mozilla CA list (fetched $MOZILLA_CA_URL)"
else
    TRUST_BUNDLE="/etc/ssl/certs/ca-certificates.crt"
    log "Trust reference: system ca-certificates.crt (Mozilla list unavailable)"
fi

# Split a PEM bundle into $TMPDIR/<prefix>_N.pem, one file per certificate.
# The prefix keeps concurrent/nested calls from clobbering each other.
split_chain() {
  local src="$1" prefix="${2:-chain}"
  rm -f "$TMPDIR/${prefix}"_*.pem
  awk -v d="$TMPDIR" -v p="$prefix" \
      '/BEGIN CERTIFICATE/{n++} {print > (d "/" p "_" n ".pem")}' "$src" 2>/dev/null || true
  ls "$TMPDIR"/${prefix}_*.pem 2>/dev/null | sort -V || true
}

# Normalise anything we downloaded (PEM bundle, PKCS#7 DER, raw DER cert)
# into a PEM bundle. Echoes the resulting path, or nothing on failure.
to_pem() {
  local src="$1" dst="$2"
  if grep -q 'BEGIN CERTIFICATE' "$src" 2>/dev/null; then
    cp "$src" "$dst" && { echo "$dst"; return 0; }
  fi
  if openssl pkcs7 -inform DER -in "$src" -print_certs -out "$dst" 2>/dev/null; then
    echo "$dst"; return 0
  fi
  if openssl x509 -inform DER -in "$src" -outform PEM -out "$dst" 2>/dev/null; then
    echo "$dst"; return 0
  fi
  if openssl pkcs7 -inform PEM -in "$src" -print_certs -out "$dst" 2>/dev/null; then
    echo "$dst"; return 0
  fi
  return 1
}

# Verify a chain file against the OS trust store.
# Usage: verify_chain <fullchain.pem>
verify_chain() {
  local chain="$1"
  local first=1 f leaf="" untrusted rc
  untrusted=$(mktemp "$TMPDIR/untrusted.XXXXXX.pem")
  : > "$untrusted"

  # Split into whole, properly-armored certs rather than stripping headers
  # with awk — openssl cannot parse a bare certificate body.
  for f in $(split_chain "$chain" "vc"); do
    if [ "$first" -eq 1 ]; then
      leaf="$f"; first=0
    else
      cat "$f" >> "$untrusted"
    fi
  done

  if [ "$first" -eq 1 ]; then
    rm -f "$untrusted"
    echo "verify_chain: no certificates found in $chain" >&2
    return 1
  fi

  # openssl verify errors out when --untrusted is empty, so skip the flag then.
  if [ ! -s "$untrusted" ]; then
    openssl verify -CAfile "$TRUST_BUNDLE" "$leaf" >/dev/null 2>&1
  else
    openssl verify -CAfile "$TRUST_BUNDLE" -untrusted "$untrusted" "$leaf" >/dev/null 2>&1
  fi
  rc=$?
  rm -f "$untrusted"
  return $rc
}

# Walk the AIA "CA Issuers" links of any cert in the bundle that does not chain,
# and append whatever issuers we find until the chain validates.
fetch_missing_issuers() {
  local chain="$1"
  local added=0
  local f url raw pem issuer_count issuer sub

  # NB: the outer list is expanded once, so nested split_chain calls use
  # distinct prefixes and cannot delete these files out from under us.
  for f in $(split_chain "$chain" "src"); do
    verify_chain "$chain" && break
    url=$(openssl x509 -in "$f" -noout -ext authorityInfoAccess 2>/dev/null \
          | grep -oE 'https?://[^ ]+\.(p7c|cer|crt|pem)' | head -1)
    [ -n "$url" ] || continue

    raw=$(mktemp "$TMPDIR/aia.XXXXXX.bin")
    if ! curl -fsSL --max-time 20 "$url" -o "$raw" 2>/dev/null; then
      rm -f "$raw"; continue
    fi

    pem=$(to_pem "$raw" "$TMPDIR/aia_XXXXXX.pem") || { rm -f "$raw"; continue; }
    rm -f "$raw"

    # A .p7c may hold several certs; keep only the one that issued this cert,
    # and only if the chain does not already contain it.
    issuer_count=$(openssl x509 -in "$f" -noout -issuer 2>/dev/null | sed 's/^issuer=//')
    PRESENT=0
    for have in $(split_chain "$chain" "have"); do
      have_sub=$(openssl x509 -in "$have" -noout -subject 2>/dev/null | sed 's/^subject=//')
      if [ -n "$issuer_count" ] && [ "$have_sub" = "$issuer_count" ]; then
        PRESENT=1; break
      fi
    done

    for sub in $(split_chain "$pem" "got"); do
      issuer=$(openssl x509 -in "$sub" -noout -subject 2>/dev/null | sed 's/^subject=//')
      [ -n "$issuer_count" ] && [ "$issuer" = "$issuer_count" ] || continue
      if [ "$PRESENT" -eq 1 ]; then
        log "  = issuer already present, skipping: $issuer"
        continue
      fi
      cat "$sub" >> "$chain"
      added=1
      log "  + fetched missing issuer via AIA: $url"
      log "    subject=$issuer"
    done
  done
  return $added
}

# ── 3. Assemble + validate fullchain.pem ──────────────────────────────────────
# NOTE: the chain may be MORE than leaf+intermediate. InCommon issues its
# OVG2C intermediate as a cross-cert, so the real path is
#   leaf -> InCommon Intermediate CA - OVG2C -> eSign Root TLS CA - G1
#        -> eSign Root CA - G1
# Serving only leaf+intermediate leaves the chain unverifiable ("x509: signed
# by unknown authority") for anything that does not chase AIA links — notably
# Grafana's infinity datasource, which fetches our own CSVs over HTTPS.
log "Assembling fullchain.pem (leaf + intermediates)..."
FULL="$INCOMING/fullchain.pem"
cat "$CERT" "$INTERM" > "$FULL"
COUNT=$(grep -c 'BEGIN CERTIFICATE' "$FULL")
[ "$COUNT" -ge 2 ] || die "Expected at least 2 certs in fullchain.pem, got $COUNT."
log "✓ fullchain.pem assembled with $COUNT certificate(s) from IT."

if verify_chain "$FULL"; then
    log "✓ Chain validates against the OS trust store."
else
    log "Chain incomplete — attempting to fetch missing issuer(s) via AIA..."
    fetch_missing_issuers "$FULL" || true
    COUNT=$(grep -c 'BEGIN CERTIFICATE' "$FULL")
    if verify_chain "$FULL"; then
        log "✓ Chain validates after AIA fetch ($COUNT certificates total)."
        log "  NOTE: IT did not supply the cross-cert. Ask them for the complete"
        log "        chain next time so this fetch is not needed."
    else
        die "Chain still does not validate. Refusing to install a broken chain.
  Run: openssl s_client -connect $DOMAIN:443 -servername $DOMAIN -showcerts </dev/null
  and ask USF IT for the full certificate chain."
    fi
fi

# ── 4. Back up current cert ───────────────────────────────────────────────────
TS=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_DIR="$REPO_DIR/certs/backup/$TS"
log "Backing up current certs to certs/backup/$TS/ ..."
mkdir -p "$BACKUP_DIR"
sudo cp -p certs/fullchain.pem certs/privkey.pem "$BACKUP_DIR/" 2>/dev/null || \
    log "WARNING: Could not back up existing certs (may not exist yet on first install)."
log "✓ Backup written."

# ── 5. Install ────────────────────────────────────────────────────────────────
log "Installing new certificates..."
sudo cp "$FULL" certs/fullchain.pem
sudo cp "$KEY"  certs/privkey.pem
sudo chown root:root certs/fullchain.pem certs/privkey.pem
sudo chmod 644 certs/fullchain.pem
sudo chmod 600 certs/privkey.pem
log "✓ Files installed."

# ── 6. Hot-reload nginx (zero downtime) ───────────────────────────────────────
log "Testing nginx config..."
docker exec nginx nginx -t \
    || { log "nginx -t FAILED. Restoring backup..."; \
         sudo cp "$BACKUP_DIR/fullchain.pem" certs/fullchain.pem; \
         sudo cp "$BACKUP_DIR/privkey.pem"   certs/privkey.pem; \
         sudo chmod 600 certs/privkey.pem; \
         docker exec nginx nginx -s reload; \
         die "nginx -t failed. Backup restored and old cert reloaded."; }

log "Reloading nginx..."
docker exec nginx nginx -s reload
log "✓ nginx reloaded (zero downtime)."

# ── 7. Verify live cert ───────────────────────────────────────────────────────
log "Verifying live certificate on $DOMAIN ..."
sleep 1   # brief pause for reload to settle

# Capture the chain the server actually presents, then verify it end to end
# against the OS trust store. Printing subject/issuer is not a verification —
# it happily reports success on a chain that cannot be built.
LIVE_CHAIN="$TMPDIR/live_chain.pem"
if openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" \
       -showcerts </dev/null 2>/dev/null \
   | awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/' > "$LIVE_CHAIN" \
   && [ -s "$LIVE_CHAIN" ]; then

    LIVE_DEPTH=$(grep -c 'BEGIN CERTIFICATE' "$LIVE_CHAIN")
    LIVE=$(openssl x509 -in "$LIVE_CHAIN" -noout -issuer -subject -dates 2>/dev/null)
    log "Live cert details:"
    echo "$LIVE" | sed "s/^/$LOG_TAG   /"
    log "  chain served: $LIVE_DEPTH certificate(s)"

    if verify_chain "$LIVE_CHAIN"; then
        log "✓ Live chain verifies against the OS trust store."
    else
        die "Live chain on $DOMAIN does NOT verify after reload.
  Browsers may still say the cert is 'up to date', but clients that do not
  chase AIA links (Grafana's infinity datasource, curl, Go) will fail with
  'x509: certificate signed by unknown authority'.
  Restore with: sudo cp certs/backup/<timestamp>/fullchain.pem certs/fullchain.pem
  then:         docker exec nginx nginx -s reload"
    fi
else
    log "WARNING: Could not reach $DOMAIN:443 from this host to verify."
    log "  Verify manually once network access is available:"
    log "  echo | openssl s_client -connect $DOMAIN:443 -servername $DOMAIN 2>/dev/null | grep 'Verify return code'"
fi

# ── 8. Clean up ───────────────────────────────────────────────────────────────
log "Removing certs/incoming/ ..."
rm -rf "$INCOMING"
log "Done. New cert valid until: $(openssl x509 -noout -enddate -in certs/fullchain.pem | cut -d= -f2)"
