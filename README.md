# mbon-dashboard-server

Docker software stack for MBON server serving early-alert dashboards.

![teaser](https://github.com/marinebon/mbon-dashboard-server/blob/main/static_files/mbon-dashboards-teaser.png)

For more detailed documentation please see `./documentation/`.

## Examples
Below is a list of "product" instances that are built with this framework.
Each "product" instance is built on a git branch in this repository, based off of the master branch.

Name                        | status                | URL                                         | Description
--------------------------- | --------------------- | --------------------------------------------| ------------
SEUS Monitoring Dash        | :heavy_check_mark: up | https://mbon-dashboards.marine.usf.edu/seus | Cram in tons of data from MBON, NERRS, & GR NMS.
FGB NMS Sentinel Sites Dash | :heavy_check_mark: up     | https://mbon-dashboards.marine.usf.edu/fgnms | Monitoring a ring of sites around the Flower Garden Banks National Marine Sanctuary where anomalously high values of chlorophyll-a concentration, for example, can be detected from satellite imagery before reaching the reefs.
FK NMS                      | :heavy_check_mark: up | https://mbon-dashboards.marine.usf.edu/fknms | Monitoring of satellite, bouy, & river discharge data around the Florida Keys National Marine Sanctuary.
FWRI SCTLD Dashboard        | :heavy_check_mark: project ended | https://mbon-dashboards.marine.usf.edu/fwc | Monitoring the spread of stony coral tissue loss disease in the Florida Keys.

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

### debugging on the grafana interface
* `502: bad gateway` error: this means that grafana can't connect to the timeseries database (influxDB).
    * check {URL}:8086/health to ensure InfluxDB okay
    * check connection urls in the config, firewalls, etc 
    * check airflow jobs to ensure ingest is working.

## requirements
* docker-compose `~> 1.28.5`. Not sure exactly the min version but `1.21.2` was tested and does not work.
* ERDDAP generally requires > 8GB memory and more is better.
