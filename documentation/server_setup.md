# Server setup

How to stand up the stack on a fresh machine. This is a single unified instance
(branch `main`); there is no longer a per-client branch/instance model — see
`documentation/archive/legacy-client-branch-setup.md` for the old approach.

```bash
# === install docker & git
sudo apt install git

curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

sudo usermod -aG docker $USER
# !!! MANUALLY LOG OUT & LOG IN to reload groups

# === get & set up the code
git clone https://github.com/marinebon/mbon-dashboard-server.git
# NOTE: for push access, set up ssh + gh auth instead:
#       ssh-keygen -t ed25519 -C "you@example.com"
#       # add ~/.ssh/id_ed25519.pub to GitHub
#       git clone git@github.com:marinebon/mbon-dashboard-server.git

cd mbon-dashboard-server
git submodule update --init --recursive     # pulls mbon_data_uploader

cp .env.example .env
# open and edit .env — set all passwords/tokens before starting

# Airflow bind-mounts use host uid/gid; match them:
echo -e "\nAIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" >> .env

# === TLS certificate
# Install the current cert into certs/ before first start.
# See documentation/hosting_details.md -> "SSL Certificate Renewal".

# === start it up
docker compose up --build -d
```

## Manual steps

### cron jobs

`crontab -e` and add:

```
# hourly: pull latest dashboard/config changes from GitHub
0  *  * * *  cd /home/murray_tylar/mbon-dashboard-server && /bin/git pull

# daily: ensure the stack is up (belt-and-suspenders)
0  11 * * *  cd /home/murray_tylar/mbon-dashboard-server && docker compose up -d
```

Certificate renewal is **not** a cron job — it is a manual, USF-IT-driven event.
See `documentation/hosting_details.md`.

### grafana-storage permissions

If Grafana fails to start with a permissions error on `grafana/grafana-storage`
(see [issue #13](https://github.com/marinebon/mbon-dashboard-server/issues/13)):

```bash
docker compose stop grafana
sudo chmod -R 777 grafana/grafana-storage
docker compose up -d grafana
```
