# Hosting Details
The SE-US MBON runs the MBON-Dashboard-Server application on Google Cloud Platform.
All supported regional dashboards are served from this single instance (running
the `main` branch), routed by URL path in `nginx/nginx.conf`. The earlier
per-client branch/instance model is retired.

Current configuration:

* Machine Config
  * E2-standard-16 instance
  * region US-east1 (South Carolina)
* OS & Storage
  * Ubuntu 24.04 LTS x86/64
  * SSD persistent disk 100GB

-------------------------------

## SSL Certificate Renewal

### How nginx consumes the cert

nginx reads two flat files, bind-mounted read-write via `./certs:/etc/nginx/certs`:

- `certs/fullchain.pem` — leaf cert + issuer chain (mode 644)
- `certs/privkey.pem` — private key (mode 600; nginx's master process runs as
  root so it can read it)

All four server blocks (443 Grafana, 8080 Airflow, 8086 InfluxDB, 5555 Flower)
point at the same two files. After the files are replaced, apply them with **zero
downtime**:

```bash
docker exec nginx nginx -t && docker exec nginx nginx -s reload
```

Never `docker stop nginx` to change certs — that is what caused the Sept 2026
outages.

### Issuance: Let's Encrypt -> eMSign, manual delivery (decided 2026-09-07)

A CAA record on the parent zone pins issuance to eMSign:

```
$ dig +short CAA marine.usf.edu
0 issue "emsign.com"
```

**Let's Encrypt can no longer issue for this domain.** History and decision:

- The old automation (`cert_update.sh` + root cron `17 0,12 * * *`) is **retired**
  as of 2026-09-07. The cron line is commented out in root's crontab (backup at
  `/root/crontab.backup-20260907`); the script is renamed
  `cert_update.sh.retired-20260907`. It failed the CAA check on every run and,
  because it stopped nginx first and used `set -e`, left the site down for hours
  after each 00:17 / 12:17 UTC run.
- The **last Let's Encrypt cert expires `Oct 5 2026 17:53 UTC`.**
- **Decision:** no self-service ACME. **USF IT issues the eMSign cert and
  delivers it to us** as the cert expiry approaches. There is no renewal cron —
  renewal is a manual, IT-driven event a few times per year. We only need a safe
  *install* procedure (below) and an expiry reminder so we chase IT in time.

#### When USF IT delivers a new cert

You will receive some combination of: the leaf certificate, the eMSign
intermediate chain, and (unless we did a CSR) the private key. Assemble two files:

- `fullchain.pem` — leaf certificate **first**, then the eMSign intermediate(s)
- `privkey.pem` — the matching private key

Install them (run from the repo dir, `~/mbon-dashboard-server`):

```bash
# 0. Put the delivered files somewhere safe, e.g. certs/incoming/
mkdir -p certs/incoming
# ...copy fullchain.pem and privkey.pem into certs/incoming/...

# 1. VALIDATE before touching anything live -------------------------------
D=mbon-dashboards.marine.usf.edu
# key matches cert (the two hashes must be identical):
sudo openssl x509 -noout -pubkey -in certs/incoming/fullchain.pem | sha256sum
sudo openssl pkey  -noout -pubout -in certs/incoming/privkey.pem  | sha256sum
# not expired, right hostname:
sudo openssl x509 -noout -dates -subject -ext subjectAltName -in certs/incoming/fullchain.pem
sudo openssl x509 -noout -checkend 0 -in certs/incoming/fullchain.pem && echo "not expired"
# chain builds to a trusted (emSign) root:
sudo openssl verify -untrusted certs/incoming/fullchain.pem certs/incoming/fullchain.pem

# 2. BACK UP the current cert -------------------------------------------
TS=$(date -u +%Y%m%dT%H%M%SZ)
sudo mkdir -p "certs/backup/$TS"
sudo cp -p certs/fullchain.pem certs/privkey.pem certs/cert.pem certs/chain.pem "certs/backup/$TS/" 2>/dev/null

# 3. INSTALL -----------------------------------------------------------
sudo cp certs/incoming/fullchain.pem certs/fullchain.pem
sudo cp certs/incoming/privkey.pem   certs/privkey.pem
sudo chown root:root certs/fullchain.pem certs/privkey.pem
sudo chmod 644 certs/fullchain.pem
sudo chmod 600 certs/privkey.pem

# 4. APPLY with zero downtime ----------------------------------------
docker exec nginx nginx -t && docker exec nginx nginx -s reload

# 5. VERIFY ----------------------------------------------------------
echo | openssl s_client -connect "$D:443" -servername "$D" 2>/dev/null \
  | openssl x509 -noout -issuer -subject -dates      # issuer should now be emSign
# repeat for :8080 :8086 :5555 — same cert file, all update on the one reload

# 6. Clean up
sudo rm -rf certs/incoming
```

If `nginx -t` fails at step 4, restore from `certs/backup/$TS/` and reload again —
nginx keeps serving the old cert until a reload succeeds, so a bad file does not
cause an outage as long as you never `docker stop` it.

> A `cert_install.sh` wrapper that runs steps 1–5 with hard validation gates can
> be added if these renewals prove frequent enough to be worth it.

#### Note on the private key

If USF IT emails the private key, treat that channel as compromised for key
purposes: ask them to deliver the key out-of-band (e.g. their secure file
transfer), or generate a CSR here so the key never leaves this host:

```bash
openssl req -new -newkey rsa:3072 -nodes \
  -keyout certs/incoming/privkey.pem \
  -out    certs/incoming/mbon-dashboards.csr \
  -subj   "/CN=mbon-dashboards.marine.usf.edu"
# hand the .csr to USF IT; they return the signed cert + chain
```

Private key material and `certs/` contents are **not** tracked in git
(`certs/.gitignore` is `*`) and must never be committed.

### Checking current cert

```bash
# On-disk file
openssl x509 -in ~/mbon-dashboard-server/certs/fullchain.pem -noout -issuer -subject -dates

# What nginx is actually serving
echo | openssl s_client -connect mbon-dashboards.marine.usf.edu:443 \
  -servername mbon-dashboards.marine.usf.edu 2>/dev/null \
  | openssl x509 -noout -issuer -subject -dates
```

-------------------------------

# Old Documentation
Below is old documentation that should probably be ignored.
Someone should come back around and clean this up.

## Create Server on DigitalOcean

Created droplet at https://digitalocean.com with ben@ecoquants.com (Google login):

- Choose an image : Distributions : Marketplace :
  - **Docker** by DigitalOcean VERSION 18.06.1 OS Ubuntu 18.04
- Choose a plan : Standard :
  - _iea-demo.us_:
    - **$20 /mo** $0.030 /hour
    - 4 GB / 2 CPUs
    - 80 GB SSD disk
    - 4 TB transfer
  - _iea-demo.us_:
    - **$40 /mo** $0.060 /hour
    - 8 GB / 4 CPUs
    - 160 GB SSD disk
    - 5 TB transfer
- Choose a datacenter region :
  - **San Francisco** (New York currently experiencing issues)
- Authentication :
  - **One-time password**
    Emails a one-time root password to you (less secure)
- How many Droplets?
  - **1  Droplet**
- Choose a hostname :
  - _iea-demo.us_:
    - **iea-demo.us**

[DigitalOcean - iea-ne.us project](https://cloud.digitalocean.com/projects/367d3107-1892-46a8-ba53-2f10b9ba1e2d/resources?i=c03c66)


Email recieved with IP and temporary password:

- _iea-demo.us_:

  > Your new Droplet is all set to go! You can access it using the following credentials:
  >
  > Droplet Name: docker-iea-demo.us
  > IP Address: 157.245.189.38
  > Username: root
  > Password: 513dbca94734429761db936640

Have to reset password upon first login.

Saved on my Mac to a local file:

```bash
ssh root@157.245.189.38
# enter password from above
# you will be asked to change it upon login
```

```bash
echo S3cr!tpw > ~/private/password_docker-iea-ne.us
cat ~/private/password_docker-iea-ne.us
```



## Setup domain iea-ne.us

- Bought domain **iea-demo.us** for **$12/yr** with account bdbest@gmail.com.

- DNS matched to server IP `64.225.118.240` to domain **iea-demo.us** via [Google Domains]( https://domains.google.com/m/registrar/iea-ne.us/dns), plus the following subdomains added under **Custom resource records** with:

- Type: **A**, Data:**157.245.189.38** and Name:
  - **@**
  - **wp**
  - **gs**
  - **rstudio**
  - **shiny**
  - **info**
  - **erddap**
  - **ckan**
- Name: **www**, Type: **CNAME**, Data:**iea-ne.us**
