The steps below are everything you need to do to stand up one of the `client-*` product branches on a fresh machine.

# Ubuntu 22.04
```bash
# ====================================================================================
# === docker install 
# ====================================================================================
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker tylarmurray  # (use your username) then restart session to reload groups
# ====================================================================================
# ====================================================================================
# === start here if you are already set up with docker-compose & git =================
# ====================================================================================
# (1) git clone the app to your local
git clone https://github.com/marinebon/mbon-dashboard-server.git -b client-CLIENT_NAME_HERE
cd mbon-dashboard-server/
git submodule update --init --recursive --remote

# (2) === app config
# open environment file
vi .env  
# & enter text based on provided example file:
# mbon-dashboard-server/documentation/example_env_file

# !!! TODO: we need to edit hostnames in docker-compose.yml ???

# Mounted vols in airflow container use the native user/group permissions,
# so the container and host computer must have matching file permissions
echo -e "\nAIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" >> .env

# (3) start it up
docker compose up --build -d

# workaround [issue #13](https://github.com/marinebon/mbon-dashboard-server/issues/13)
sudo chmod -R 777 grafana/grafana-storage
docker-compose up --build -d
```

Don't forget the manual steps at the bottom of this doc!

# CentOS 8
```bash
# ====================================================================================
# === docker & git setup steps =======================================================
# ====================================================================================
# install docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker tylarmurray  # (use your username) then restart session to reload groups

# install docker-compose
 sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
 sudo chmod +x /usr/local/bin/docker-compose

# install git
sudo yum install -y git

# ====================================================================================
# === start here if you are already set up with docker-compose & git =================
# ====================================================================================
# (1) git clone the app to your local
git clone https://github.com/marinebon/mbon-dashboard-server.git -b client-CLIENT_NAME_HERE
cd mbon-dashboard-server/
git submodule update --init --recursive --remote

# (2) === app config
# open environment file
vi .env  
# & enter text based on provided example file:
# mbon-dashboard-server/documentation/example_env_file

# !!! TODO: we need to edit hostnames in docker-compose.yml ???

# Mounted vols in airflow container use the native user/group permissions,
# so the container and host computer must have matching file permissions
echo -e "\nAIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" >> .env

# (3) init databases
docker-compose up airflow-init
# After completed you should see "start_airflow-init_1 exited with code 0".
# The airflow account created has the login airflow and the password airflow.

# (4) start it up
docker-compose up --build -d

# workaround [issue #13](https://github.com/marinebon/mbon-dashboard-server/issues/13)
sudo chmod -R 777 grafana/grafana-storage
docker-compose up --build -d
```
Don't forget the manual steps at the bottom of this doc!

# set grafana "home dashboard"
Now for the manual steps:

1. open grafana (http://35.209.104.85:3000) & bottom left click "sign in"
2. sign in with `imars_grafana_user` and pw from `.env` (`grafana_admin_pw`)
3. now @ grafana home in top left click "home" > "home dashboard"
4. top right(ish) click star to "star" the dashboard
5. left side click the cog > "preferences" 
6. now in org config set "home dashboard" to "Home Dashboard" & click save 
