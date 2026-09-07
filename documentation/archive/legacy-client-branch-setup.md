# Legacy: per-client-branch setup (DEPRECATED)

> **Deprecated.** The project no longer deploys a separate `client-*` branch per
> machine. Everything runs from one unified stack on `main` (see
> `documentation/server_setup.md`). Kept for historical reference only; commands
> below use the legacy hyphenated `docker-compose` v1 and `-b client-*` clones.

The steps below stood up one of the `client-*` product branches on a fresh machine.

## Ubuntu 22.04

```bash
# === docker install ===
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"   # then restart session to reload groups

# === app (assumes docker + git ready) ===
git clone https://github.com/marinebon/mbon-dashboard-server.git -b client-CLIENT_NAME_HERE
cd mbon-dashboard-server/
git submodule update --init --recursive --remote

# app config
vi .env    # based on .env.example
# !!! historically also had to edit hostnames in docker-compose.yml

echo -e "\nAIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" >> .env

docker compose up --build -d

# workaround issue #13
sudo chmod -R 777 grafana/grafana-storage
docker compose up --build -d
```

## CentOS 8

```bash
# === docker & git ===
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker "$USER"   # then restart session to reload groups

sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo yum install -y git

# === app (assumes docker + git ready) ===
git clone https://github.com/marinebon/mbon-dashboard-server.git -b client-CLIENT_NAME_HERE
cd mbon-dashboard-server/
git submodule update --init --recursive --remote

vi .env    # based on .env.example
echo -e "\nAIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" >> .env

docker compose up airflow-init
# expect "start_airflow-init_1 exited with code 0"; default airflow/airflow login

docker compose up --build -d

# workaround issue #13
sudo chmod -R 777 grafana/grafana-storage
docker compose up --build -d
```
