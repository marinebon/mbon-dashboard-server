# mbon-dashboard-server

Docker software stack for MBON server serving early-alert dashboards.

![teaser](https://github.com/marinebon/mbon-dashboard-server/blob/main/static_files/mbon-dashboards-teaser.png)

For more detailed documentation see [`documentation/`](documentation/README.md).

## Dashboards
All dashboards are served from a single stack at `https://mbon-dashboards.marine.usf.edu`,
routed by URL path in `nginx/nginx.conf`:

| Path              | Dashboard                                   | Notes |
| ----------------- | ------------------------------------------- | ----- |
| `/seus`, `/grnms` | SE-US / Gray's Reef NMS Early Alert         | data from MBON, NERRS, & GR NMS |
| `/fknms`, `/fk`   | Florida Keys NMS Early Alert                | satellite, buoy, & river-discharge data |
| `/fgbnms`         | Flower Garden Banks NMS Sentinel Sites      | detects anomalous satellite chlorophyll-a around the FGB reefs |
| `/fwc`            | FWC Coral Disease (SCTLD)                   | project ended; route retained |

Historically each dashboard was a separate `client-*` git branch deployed on its
own machine. Those branches are kept for history, but the current deployment is
one unified stack on `main`.

## Directory Structure Overview
`docker-compose.yml` handles most configuration.
The subdirectories (eg `grafana/`, `nginx/`, `airflow/`) contain container-specific files.

## Setup
### General Setup Notes
In general you will configure your stack by:
1. Modifying `docker-compose.yml` and container-specific configuration files inside of `./grafana/`, `./nginx/`, `./airflow/`, etc.
    Directions for this is included within a `README.md` file inside of each directory.
    Changes made to these files should be version controlled using git.
2. Setting up docker volumes so that data can persist when containers are recreated.
    Volumes are generally too large for git, so you should manage backups of these directories.
    A strategy for this is not included.
3. Setting passwords & configuration in `.env` (copy `.env.example` as a starting point).
    This file should not be added to git for security reasons.
    A backup strategy for this file is not included.

### debugging on the grafana interface
* `502: bad gateway` error: this means that grafana can't connect to the timeseries database (influxDB).
    * check {URL}:8086/health to ensure InfluxDB okay
    * check connection urls in the config, firewalls, etc 
    * check airflow jobs to ensure ingest is working.

## requirements
* Docker Engine with the Compose v2 plugin (invoked as `docker compose`; the legacy hyphenated `docker-compose` v1 is not supported).
* ~8 GB RAM minimum for the full stack (InfluxDB + Airflow workers + Grafana + Postgres/Redis).
