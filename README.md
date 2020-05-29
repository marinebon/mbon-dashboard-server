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

## Basic Setup
1. clone this repo
2. install docker & docker-compose
3. add permissions to run docker for current user
    1. `sudo usermod -aG docker ${USER}`
3. adjust settings
    1. set passwords in the environment `.env` file.
        * see the `documentation/example_env_file` for an example.
    2. set `baseUrl` & `baseHttpsUrl` in `erddap/setup.xml`
        * should be `localhost` or your server hostname
    3. the permissions on the following directories need to be set
        * `chmod 777 grafana/grafana_data`
3. start everything up: `docker-compose up --build -d`
4. test it out (assuming your hostname is "localhost")
    1. http://localhost/ should show "welcome to nginx"
    2. http://localhost:8080/ should show a 404 from tomcat
    3. http://localhost:8080/erddap should show ERDDAP's page
    4. http://localhost:8086/ should show "404 page not found" from InfluxDB
    5. http://localhost:3000/login should show grafana login
5. configure grafana
    * import dashboards from [github/USF-IMaRS/grafana-dashboards](https://github.com/USF-IMARS/grafana-dashboards) using [these instructions.](https://grafana.com/docs/grafana/latest/reference/export_import/#importing-a-dashboard)

## Basic Workflow
1. modify `docker-compose.yml` or files within container folders
2. `docker-compose up --build -d` to update what's running
3. `git pull` then `git commit` your changes
    * do not commit your `.env` or hostname changes to `erddap/setup.xml`
