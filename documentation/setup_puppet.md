This checklist is for setting up an IMaRS VM running docker and managed by puppet.

1. create & configure base CentOS 7 VM (see centos_base VM using virt-manager)
2. install docker. ref: https://docs.docker.com/engine/install/centos/
2. install latest docker-compose
    * `sudo curl -L "https://github.com/docker/compose/releases/download/1.26.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose`
    * `sudo chmod +x /usr/local/bin/docker-compose`
3. `git clone https://github.com/marinebon/mbon-dashboard-server -b client-fwc`
3. `git submodule update --init --recursive --remote`
3. `cd docker_volumes/mbon-dashboard-server/`
4. create or upload an `.env` file in mbon-dashboard-server dir
    * eg: `scp .env root@fgbnms-dashboard:docker_volumes/mbon-dashboard-server/.`
5. `docker-compose up -d --build`
