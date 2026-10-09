# certs/

This directory holds the TLS certificate and key served by nginx.

All files here are **excluded from git** (`certs/.gitignore` contains `*`).
Never commit cert or key material.

---

## Files nginx uses

| File | Purpose | Mode |
|------|---------|------|
| `fullchain.pem` | Leaf cert + InCommon intermediate (assembled from IT-delivered files) | 644 |
| `privkey.pem` | Matching private key | 600 |

nginx bind-mounts this directory as `./certs:/etc/nginx/certs`.
All four TLS server blocks (ports 443, 8080, 8086, 5555) read the same two files.

---

## Cert issuance

Certificates are issued by **eMSign / InCommon** via USF IT.
(Let's Encrypt is blocked — a CAA record on `marine.usf.edu` pins issuance to `emsign.com`.)
Renewal is a manual, IT-driven event. **There is no renewal cron job.**
Chase IT a few weeks before expiry.

Check the current cert expiry:

```bash
# What's on disk:
openssl x509 -in ~/mbon-dashboard-server/certs/fullchain.pem -noout -dates

# What nginx is actually serving:
echo | openssl s_client -connect mbon-dashboards.marine.usf.edu:443 \
  -servername mbon-dashboards.marine.usf.edu 2>/dev/null \
  | openssl x509 -noout -dates
```

---

## What USF IT delivers

IT sends a zip containing (at minimum):

| Filename pattern | Contents |
|-----------------|---------|
| `*_cert.cer` | Leaf certificate (PEM) |
| `*_interm.cer` | InCommon intermediate certificate (PEM) |
| `*.key` | Private key (PKCS#8 PEM, `-----BEGIN PRIVATE KEY-----`) |
| `*.csr` | Certificate Signing Request (reference only, not needed for install) |
| `*.cnf` | OpenSSL config used to generate the CSR (reference only) |

You need to assemble `fullchain.pem` from the two `.cer` files before installing.

---

## Installing a new cert

### Step 0 — Upload files from your laptop

Run from your **laptop** (requires the `gcloud` CLI):

```bash
# Create the staging dir on the server (if it doesn't exist)
gcloud compute ssh murray_tylar@<INSTANCE_NAME> -- \
    "mkdir -p ~/mbon-dashboard-server/certs/incoming"

# Copy the IT-delivered files up (adjust filenames to match what you received)
gcloud compute scp \
    mbon-dashboards_marine_usf_edu_cert.cer \
    mbon-dashboards_marine_usf_edu_interm.cer \
    mbon-dashboards_marine_usf_edu.key \
    murray_tylar@<INSTANCE_NAME>:~/mbon-dashboard-server/certs/incoming/
```

`<INSTANCE_NAME>` is the VM name shown in the GCP console.
Add `--zone <ZONE>` if prompted (e.g. `--zone us-east1-b`).

Alternative using plain `scp` (you need the external IP from the GCP console):

```bash
scp mbon-dashboards_marine_usf_edu_cert.cer \
    mbon-dashboards_marine_usf_edu_interm.cer \
    mbon-dashboards_marine_usf_edu.key \
    murray_tylar@<EXTERNAL_IP>:~/mbon-dashboard-server/certs/incoming/
```

---

### Steps 1–5 — run the install script

With the files in `certs/incoming/`, just run:

```bash
cd ~/mbon-dashboard-server
make cert-update
# or: bash cert_install.sh
```

The script auto-detects the `*_cert.cer`, `*_interm.cer`, and `*.key` files,
then validates → assembles → backs up → installs → hot-reloads nginx → verifies
→ cleans up, all in one shot.

Backup of the previous cert is written to `certs/backup/<timestamp>/` before
anything is changed. If `nginx -t` fails the script restores the backup
automatically and the old cert keeps serving — no outage.

> **Never `docker stop nginx` to change certs.**

---

## What `cert_install.sh` does (step by step)

For reference / manual fallback:

1. **Auto-detect** `*_cert.cer`, `*_interm.cer`, `*.key` in `certs/incoming/`
2. **Validate key ↔ cert** — compares RSA modulus hashes (uses `openssl rsa`, not
   `openssl pkey`, for PKCS#8 PEM keys from InCommon)
3. **Check expiry** — aborts if cert is already expired
4. **Assemble** `fullchain.pem` = leaf + intermediate (2 certs)
5. **Back up** current `fullchain.pem` + `privkey.pem` to `certs/backup/<timestamp>/`
6. **Install** with correct ownership (`root:root`) and permissions (644 / 600)
7. **Hot-reload** nginx (`nginx -t && nginx -s reload`); auto-restores backup if `-t` fails
8. **Verify** the live cert via `openssl s_client`
9. **Clean up** `certs/incoming/`

Note: `openssl verify` prints "error 20: unable to get local issuer certificate"
because the emSign root is not in Ubuntu's trust store. This is expected —
browsers trust it natively. The script skips that check and uses live `s_client`
verification instead.

---

## Current cert (this renewal — Oct 2026)

| Field | Value |
|-------|-------|
| Issued to | `mbon-dashboards.marine.usf.edu` |
| Issuer | InCommon Intermediate CA - OVG2C → emSign Root TLS CA - G1 |
| Valid from | Sep 24 2026 |
| Valid until | **Apr 11 2027** |

---

## More detail

See `documentation/hosting_details.md` → "SSL Certificate Renewal" for full history,
decision rationale, and CSR generation instructions.
