updated 2020-07-16

1. install docker & docker-compose
1. git clone
1. git submodule update --init --recursive --remote
1. set passwords in the environment `.env` file.
1. set hostname(s) in `docker-compose.yml`
1. open relevant ports on the hypervisor (see `docker-compose.yml` for port numbers)
2. docker-compose up -d --build
3. open grafana GUI
    1. go to the "Home Dashboard"
    2. star the Home Dashboard
    1. go to configuration(cog) / Preferences
    2. set "Home Dashboard" to from "Default" to "Home Dashboard" & save
