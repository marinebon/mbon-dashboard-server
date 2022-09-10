#!/bin/bash
#
# This is a helper script used to reset the whole docker stack.
# Run it to nuke everything and start over completely fresh.
# Note that this does no checks and following along with the steps in the
# README.md is what you *should* be doing.
# If you are using this then you are being lazy and you should be ashamed.

# === nuke
docker-compose down --volumes --rmi all

sudo rm -rf ./airflow/logs/*
git checkout ./airflow/logs/.gitignore

sudo rm -rf ./erddap/erddap_data/*
git checkout ./erddap/erddap_data/.gitignore

sudo rm -rf ./grafana/grafana-storage/*
git checkout ./grafana/grafana-storage/.gitignore

sudo rm -rf ./influxdb/data_volume/*
git checkout ./influxdb/data_volume/.gitignore

sudo rm -rf ./postgres/pgdata
mkdir ./postgres/pgdata

# === init
docker-compose up airflow-init

# === start
docker-compose up --build -d

# === workaround [issue #13](https://github.com/marinebon/mbon-dashboard-server/issues/13)
echo contemplating the ethics of laziness...
sleep 10
sudo chmod -R 777 grafana/grafana-storage
docker-compose up --build -d
