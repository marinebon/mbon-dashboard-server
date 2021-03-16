The steps below are everything you need to do to stand up one of the `client-*` product branches on a fresh CentOS 8 machine.

```bash
# ====================================================================================
# === standard docker & git steps ====================================================
# ====================================================================================
# install docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo usermod -aG docker  # then restart session to reload groups

# install docker-compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.28.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# install git
sudo yum install -y git

# ====================================================================================
# === start here if you are already set up with docker-compose & git =================
# ====================================================================================
# git clone the app to your local
git clone https://github.com/marinebon/mbon-dashboard-server.git -b client-fwc3
cd mbon-dashboard-server/
git submodule update --init --recursive --remote

# app config
vi .env  # & enter text based on provided example file
mkdir ./postgres/pgdata
# TODO: we need to edit hostnames in docker-compose.yml ???

# init databases
docker-compose -f docker-compose-init.yml up -d  
# wait a couple minutes for the init containers to do their job
docker-compose -f docker-compose-init.yml down

# start it up
docker-compose up --build -d

# workaround [issue #13](https://github.com/marinebon/mbon-dashboard-server/issues/13)
chmod -R 777 grafana/grafana-storage
docker-compose up --build -d
```

