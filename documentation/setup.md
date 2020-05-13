

## Install Docker

Since we used an image with `docker` and `docker-compose` already installed, we can skip this step.

References:

- [How To Install and Use Docker on Ubuntu 18.04 | DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-18-04) for more.

```bash
sudo apt install apt-transport-https ca-certificates curl software-properties-common

# add the GPG key for the official Docker repository to your system
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# add the Docker repository to APT sources
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"

# update the package database with the Docker packages from the newly added repo
sudo apt update

# install Docker
sudo apt install docker-ce



### docker

```bash
# confirm architecture
uname -a
# Linux docker-iea-ne 4.15.0-58-generic #64-Ubuntu SMP Tue Aug 6 11:12:41 UTC 2019 x86_64 x86_64 x86_64 GNU/Linux

# update packages
sudo apt update

# check that it’s running
sudo systemctl status docker

# add permissions to run docker for current user
sudo usermod -aG docker ${USER}
```

### docker-compose

References:

- [How To Install Docker Compose on Ubuntu 18.04 | DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-install-docker-compose-on-ubuntu-18-04)

```bash
# check for latest version at https://github.com/docker/compose/releases and update in url
sudo curl -L https://github.com/docker/compose/releases/download/1.25.5/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose

# set the permissions
sudo chmod +x /usr/local/bin/docker-compose

# verify that the installation was successful by checking the version:
docker-compose --version
# docker-compose version 1.25.4, build 8d51620a
```


- [Install Docker Compose | Docker Documentation](https://docs.docker.com/compose/install/)


## Build containers

### Test webserver

Reference:

- [How To Run Nginx in a Docker Container on Ubuntu 14.04 | DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-run-nginx-in-a-docker-container-on-ubuntu-14-04)

```bash
docker run --name test-web -p 80:80 -d nginx

# confirm working
docker ps
curl http://localhost
```

returns:
```
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>Welcome to nginx!</h1>
<p>If you see this page, the nginx web server is successfully installed and
working. Further configuration is required.</p>

<p>For online documentation and support please refer to
<a href="http://nginx.org/">nginx.org</a>.<br/>
Commercial support is available at
<a href="http://nginx.com/">nginx.com</a>.</p>

<p><em>Thank you for using nginx.</em></p>
</body>
</html>
```

Turn off:

```bash
docker stop test-web
```


## Run docker-compose

References:

- [Quickstart: Compose and WordPress | Docker Documentation](https://docs.docker.com/compose/wordpress/)
- [docker-compose.yml · kartoza/docker-geoserver](https://github.com/kartoza/docker-geoserver/blob/master/docker-compose.yml)
- [How To Install WordPress With Docker Compose | DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-install-wordpress-with-docker-compose)


First, you will create the environment `.env` file to specify password and host:

- NOTE: Set `PASSWORD`, substituting "S3cr!tpw" with your password. The [docker-compose.yml](https://github.com/BenioffOceanInitiative/s4w-docker/blob/master/docker-compose.yml) uses [variable substitution in Docker](https://docs.docker.com/compose/compose-file/#variable-substitution).

```bash
# get latest docker-compose files
git clone https://github.com/marinebon/mbon-dashboard-server.git
cd ~/mbon-dashboard-server

# set environment variables
echo "PASSWORD=S3cr!tpw" > .env
echo "HOST=mbon.marine.usf.edu" >> .env
cat .env

# launch
docker-compose up -d

# Creating network "iea-server_default" with the default driver
# Creating volume "iea-server_postgis-backups" with default driver
# Creating volume "iea-server_geoserver-data" with default driver
# Creating volume "iea-server_postgis-data" with default driver
# Creating volume "iea-server_mysql-data" with default driver
# Creating volume "iea-server_wordpress-html" with default driver
# Creating volume "iea-server_shiny-apps" with default driver
# Creating volume "iea-server_erddap-data" with default driver
# Creating volume "iea-server_erddap-config" with default driver
# Creating volume "iea-server_nginx-html" with default driver
# Pulling postgis (kartoza/postgis:11.0-2.5)...
# 11.0-2.5: Pulling from kartoza/postgis
# 68ced04f60ab: Pull complete
# ...

# OR update
git pull; docker-compose up -d

# OR build if Dockerfile updated in subfolder
git pull; docker-compose up --build -d

# git pull; docker-compose up -d --no-deps --build erddap

# OR reload
docker-compose restart

# OR stop
docker-compose stop
```


### Push docker image

Since rstudio-shiny is a custom image `bdbest/rstudio-shiny:s4w`, I [docker-compose push](https://docs.docker.com/compose/reference/push/) to [bdbest/rstudio-shiny:s4w | Docker Hub](https://hub.docker.com/layers/bdbest/rstudio-shiny/s4w/images/sha256-134b85760fc6f383309e71490be99b8a50ab1db6b0bc864861f9341bf6517eca).

```bash
# login to docker hub
docker login --username=bdbest

# push updated image
docker-compose push
```

### Develop on local host

Note setting of `HOST` to `local` vs `iea-ne.us`:

```bash
# get latest docker-compose files
git clone https://github.com/marinebon/iea-server.git
cd ~/iea-server

# set environment variables
echo "PASSWORD=S3cr!tpw" > .env
echo "HOST=iea-ne.us" >> .env
cat .env

# launch
docker-compose up -d

# see all containers
docker ps -a
```

Then visit http://localhost or http://rstudio.localhost.

TODO: try migrating volumes in /var/lib/docker onto local machine.


### Operate on all docker containers

```bash
# stop all running containers
docker stop $(docker ps -q)

# remove all containers
docker rm $(docker ps -aq)

# remove all image
docker rmi $(docker images -q)

# remove all volumes
docker volume rm $(docker volume ls -q)

# remove all stopped containers
docker container prune
```



## erddap quick fix

```bash
# get inside erddap docker instance
docker exec -it erddap bash

# install editor
apt-get update
apt-get install vim

# edit setup.xml
cd /usr/local/tomcat/content/erddap
vi setup.xml

# exit from erddap container
exit

# restart erddap container
docker restart erddap

# yay! working at http://mbon.marine.usf.edu:8080/erddap
# so copy working setup.xml into docker
docker cp \
  erddap:/usr/local/tomcat/content/erddap/setup.xml \
  /home/bbest/mbon-dashboard-server/erddap/setup.xml

# (after git commit), refetch and run again
git pull
docker-compose up --build -d

# check log files
docker exec -it erddap more /erddapData/logs/log.txt
```

Edits in `setup.xml`:
- `baseUrl: from `localhost` to `mbon.marine.usf.edu`
- `baseHttpsUrl: from `localhost` to `mbon.marine.usf.edu`

Voila! http://mbon.marine.usf.edu:8080/erddap/index.html



```bash
git pull

nc_local=./erddap/data/iea-ne/ex-chl-ppd/M_201901-MODISA-NESGRID-CHLOR_A.nc
nc_docker=erddap:/erddapData/iea-ne/ex-chl-ppd/M_201901-MODISA-NESGRID-CHLOR_A.nc
docker exec erddap bash -c "mkdir -p /erddapData/iea-ne/ex-chl-ppd"
docker exec erddap bash -c "mkdir -p /usr/local/tomcat/conf/Catalina/localhost"
docker cp $nc_local $nc_docker

docker exec -it erddap bash -c "cd /usr/local/tomcat/webapps/erddap/WEB-INF && bash GenerateDatasetsXml.sh -verbose"
```
Doh! Still Bad Gateway at http://erddap.iea-demo.us/

```
Parameters for loading M_201901-MODISA-NESGRID-CHLOR_A.nc using:
GenerateDatasetsXml.sh -verbose

- Which EDDType: EDDGridFromNcFiles
- Parent directory: /erddapData/iea-ne/ex-chl-ppd
- File name regex: .*\.*nc
- Full file name of one file: /erddapData/iea-ne/ex-chl-ppd/M_201901-MODISA-NESGRID-CHLOR_A.nc
- ReloadEveryNMinutes: 10
- cacheFromUrl:
^D
```
