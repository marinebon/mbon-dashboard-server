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
# TODO: we need to edit hostnames in docker-compose.yml ???

# Mounted vols in airflow container use the native user/group permissions,
# so the container and host computer must have matching file permissions
echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" > .env

# init databases
docker-compose up airflow-init
# After completed you should see "start_airflow-init_1 exited with code 0".
# The airflow account created has the login airflow and the password airflow.

# start it up
docker-compose up --build -d

# workaround [issue #13](https://github.com/marinebon/mbon-dashboard-server/issues/13)
sudo chmod -R 777 grafana/grafana-storage
docker-compose up --build -d
```
