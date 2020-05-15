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
        Contents should resemble:
        ```
        PASSWORD="S3cr!tpw"
        HOST="mbon.marine.usf.edu"
        ```
    2. set `baseUrl` & `baseHttpsUrl` in `erddap/setup.xml`
        * should be `localhost` or your server hostname
3. start everything up: `docker-compose up --build -d`
4. test it out (assuming your hostname is "localhost")
    1. http://localhost/ should show "welcome to nginx"
    2. http://localhost:8080/ should show a 404 from tomcat
    3. http://localhost:8080/erddap should show ERDDAP's page

## Basic Workflow
1. modify `docker-compose.yml` or files within container folders
2. `docker-compose up --build -d` to update what's running
3. `git pull` then `git commit` your changes
    * do not commit your `.env` or hostname changes to `erddap/setup.xml`
