# mbon-dashboard-server

Server software stack for MBON server serving early-alert dashboards.

Contents:
<!--
To update table of contents run: `./gh-md-toc README.md` & copy the output
Uses: https://github.com/ekalinin/github-markdown-toc
-->

For detailed documentation please see `./documentation/`.

## Project Structure Overview
`docker-compose.yml` handles most configuration.
The subdirectories (eg erddap, nginx, etc) contain container-specific files.

## Setup
### General Setup Notes
In general you will configure your stack by:
1. Modifying `docker-compose.yml` and container-specific configuration files inside of `./erddap/`, `./grafana/`, etc.
    Directions for this is included within a `README.md` file inside of each directory.
    Changes made to these files should be version controlled using git.
2. Setting up docker volumes so that data can persist when containers are recreated.
    Volumes are generally too large for git, so you should manage backups of these directories.
    A strategy for this is not included.
3. Setting passwords & configuration in `.env`.
    This file should not be added to git for security reasons.
    A backup strategy for this file is not included.

It is suggested that you configure each container one-at-a-time.
To do this simply comment out the relevant sections of docker-compose.yml.

### Setup Checklist
1. fork this repo & clone your fork to local machine
2. install docker & docker-compose
3. add permissions to run docker for current user
    1. `sudo usermod -aG docker ${USER}`
3. adjust settings
    1. set passwords in the environment `.env` file.
        * see the `documentation/example_env_file` for an example.
    2. connect ERDDAP to your data - see `./erddap/README.md`
    3. load data into InfluxDB - see `./influxdb/README.md`
    4. modify grafana dashboards - see `./grafana/README.md`
3. start everything up: `docker-compose up --build -d`
4. test it out (assuming your hostname is "localhost")
    1. http://localhost/ should show "welcome to nginx"
    2. http://localhost:8080/ should show a 404 from tomcat
    3. http://localhost:8080/erddap should show ERDDAP's page
    4. http://localhost:8086/ should show "404 page not found" from InfluxDB
    5. http://localhost:3000/login should show grafana login
    6. http://localhost:5000 should show a data submission form from mbon_data_uploader

## Basic Workflow
1. modify `docker-compose.yml` or files within container folders
2. `docker-compose up --build -d` to update what's running
3. `git pull` then `git commit` your changes
    * do not commit your `.env` or hostname changes to `erddap/setup.xml`
