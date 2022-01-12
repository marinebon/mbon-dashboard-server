#!/bin/bash
#
# This is a helper script used to reset the whole docker stack.
# Run it to nuke everything and start over completely fresh.
# Note that this does no checks and following along with the steps in the
# README.md is what you *should* be doing.
# If you are using this then you are being lazy and you should be ashamed.

# nuke
docker-compose down --volumes --rmi all
# init
docker-compose up airflow-init
# start
docker-compose up --build -d
# workaround [issue #13](https://github.com/marinebon/mbon-dashboard-server/issues/13)
echo contemplating the ethics of laziness...
sleep 10
sudo chmod -R 777 grafana/grafana-storage
docker-compose up --build -d
