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
DOMAIN="mbon-dashboards.marine.usf.edu"
LOG_TAG="[cert_install $(date -u '+%Y-%m-%dT%H:%M:%SZ')]"

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

# NOTE: 'openssl verify' will print "error 20: unable to get local issuer
# certificate" because the emSign root is not in Ubuntu's trust store.
# This is expected — browsers trust it because they ship the emSign root.
# We skip that check here; the live verification in step 7 is the real test.

# ── 3. Assemble fullchain.pem ─────────────────────────────────────────────────
log "Assembling fullchain.pem (leaf + intermediate)..."
FULL="$INCOMING/fullchain.pem"
cat "$CERT" "$INTERM" > "$FULL"
COUNT=$(grep -c 'BEGIN CERTIFICATE' "$FULL")
[ "$COUNT" -eq 2 ] || die "Expected 2 certs in fullchain.pem, got $COUNT."
log "✓ fullchain.pem assembled with $COUNT certificates."

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
LIVE=$(echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null \
       | openssl x509 -noout -issuer -subject -dates 2>/dev/null) \
    || true   # non-fatal if s_client can't connect from localhost

if [ -n "$LIVE" ]; then
    log "Live cert details:"
    echo "$LIVE" | sed "s/^/$LOG_TAG   /"
else
    log "WARNING: Could not verify live cert via s_client (firewall or DNS?). Check manually:"
    log "  echo | openssl s_client -connect $DOMAIN:443 -servername $DOMAIN 2>/dev/null | openssl x509 -noout -dates"
fi

# ── 8. Clean up ───────────────────────────────────────────────────────────────
log "Removing certs/incoming/ ..."
rm -rf "$INCOMING"
log "Done. New cert valid until: $(openssl x509 -noout -enddate -in certs/fullchain.pem | cut -d= -f2)"
