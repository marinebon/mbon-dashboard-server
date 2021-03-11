# mbon-dashboard-server

Docker software stack for MBON server serving early-alert dashboards.

For more detailed documentation please see `./documentation/`.

## Repository "framework" & "product" organization
Herein we use the terms dashboard *"framework"* for something that people can use to build their own *"products"*.
An example *product*: "A dashboard so show fish population correlated with nutrient data and satellite imagery".
Versus the *framework*: "The stack that someone could install, configure, and populate the DB to build the aforementioned product."

The "master" branch of the repository is the framework used to build products. 
This framework contains the common core of software configuration and setup for any product build.

The `client-*` branches (eg client-fgbnms, client-fk_water_quality, client-fknms, client-fwc) are products ready to be cloned built with minimal configuration.

For details on how to work within this organizational setup see the [basic-workflow section](https://github.com/marinebon/mbon-dashboard-server#basic-workflow) below.

## Directory Structure Overview
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
4. Adjust settings. Products built on the mbon-dashboard-server base framework (like the FKNMS dashboard on the `client-fknms` branch) will already have configuration for these set up. Please take the **REQUIRED** steps below and use the **OPTIONAL** configuration options to further customize your usage as needed.
    1. **REQUIRED** set passwords in the environment `.env` file.
        * see the `documentation/example_env_file` for an example.
    2. **REQUIRED**: create data dir for PostgreSQL - see `./postgres/README.md`
    3. **OPTIONAL:** connect ERDDAP to your data - see `./erddap/README.md`
    4. **OPTIONAL**: load data into InfluxDB - see `./influxdb/README.md`
    5. **OPTIONAL:** modify grafana dashboards - see `./grafana/README.md`
5. run initialization containers:
    1. `docker-compose -f docker-compose-init.yml up -d`
    2. wait a few minutes
    3. `docker-compose -f docker-compose-init.yml down`
6. start everything up: `docker-compose up --build -d`
7. **REQUIRED**: toggle "on" airflow processing DAGs - see [issue #12](https://github.com/marinebon/mbon-dashboard-server/issues/12)
8. test it out (assuming your hostname is "localhost")
    1. http://localhost/ should show "welcome to nginx"
    2. http://localhost:8080/ should show a 404 from tomcat
    3. http://localhost:8080/erddap should show ERDDAP's page
    4. http://localhost:8086/ should show "404 page not found" from InfluxDB
    5. http://localhost:3000/login should show grafana login
    6. http://localhost:5000 should show a data submission form from mbon_data_uploader
    7. http://localhost:8888 should show airflow login & admin dashboard after logging in

## Basic Workflow
The workflow here is to do any non-site-specific work on the master branch.
Each client installation then has a `client-*` branch coming off of the master branch.
To update a client branch to use the latest master `git rebase` is used.

### Editing master
1. modify `docker-compose.yml` or files within container folders
2. `docker-compose up --build -d` to update what's running
3. `git pull` then `git commit` your changes
    * do not commit your `.env` or hostname changes to `erddap/setup.xml`
    
### Editing client branch
1. same as above
2. same as above
3. `git checkout client-fknms`
4. `git rebase master`
5. resolve any merge issues
6. `git push -f origin client-fknms`  
    * !!! be careful with force pushing; it deletes history
