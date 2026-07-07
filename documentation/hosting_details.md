# Hosting Details
The SE-US MBON runs the MBON-Dashboard-Server application on Google Cloud Platform.
As of 2025, all supported regional dashboards are being integrated into a single instance under the branch `unify-subdomain`.
For the ~4 client organizations the following configuration is being used:

* Machine Config
  * E2-standard-16 instance
  * region US-east1 (South Carolina)
* OS & Storage
  * Ubuntu 24.04 LTS x86/64
  * SSD persistent disk 100GB

-------------------------------

## SSL Certificate Renewal

TLS certificates for `mbon-dashboards.marine.usf.edu` are issued by **Let's Encrypt** and managed via `certbot/certbot` running in a Docker container.

Certificates expire every **90 days**. Renewal is handled automatically by a root cron job that runs twice daily.

### Automated Renewal (cron)

The renewal is configured in **root's crontab** (`sudo crontab -e`):

```
17 0,12 * * * /bin/bash /home/murray_tylar/mbon-dashboard-server/cert_update.sh >> /var/log/cert_update.log 2>&1
```

- Runs at **00:17 and 12:17 UTC every day** (offset from the hour to reduce Let's Encrypt load)
- Certbot only renews when the cert has **< 30 days remaining**, so the twice-daily schedule provides retry opportunities without spamming the CA
- All output is logged to **`/var/log/cert_update.log`**

### How `cert_update.sh` Works

1. Stops the `nginx` container to free port 80
2. Runs certbot standalone to complete the ACME HTTP-01 challenge
3. Copies the renewed certs (using `-L` to dereference Let's Encrypt symlinks) from `certs/live/<domain>/` into the flat `certs/` directory that nginx reads
4. Restarts nginx with `docker compose up --build -d nginx`

### Checking Renewal Status

```bash
# View recent renewal log
sudo tail -50 /var/log/cert_update.log

# Check current cert expiry
openssl x509 -in ~/mbon-dashboard-server/certs/fullchain.pem -noout -dates
```

### Manual Renewal (if cert is expired)

If the cert has already expired, run the script manually as root:

```bash
sudo bash /home/murray_tylar/mbon-dashboard-server/cert_update.sh
```

> **Note:** If certbot reports the cert is not yet due for renewal but it is already expired or within the 30-day window, add `--force-renewal` to the `docker run` command inside `cert_update.sh` temporarily, run it, then remove the flag.

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
