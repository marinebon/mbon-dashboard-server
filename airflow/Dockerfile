FROM apache/airflow:latest

ARG INFLUXDB_HOSTNAME
ARG INFLUXDB_TOKEN

USER root
# =============================================================

# === install git + pip
RUN apt-get update && \
    apt-get install --yes git python3-pip

# === install influxdb
RUN curl -O https://dl.influxdata.com/influxdb/releases/influxdb2-client-2.3.0-linux-amd64.tar.gz && \
    tar xvzf influxdb2-client-2.3.0-linux-amd64.tar.gz && \
    cp influxdb2-client-2.3.0-linux-amd64/influx /usr/local/bin/

USER airflow
# ===========================================================

# === install python dependencies from requirements.txt
ADD requirements.txt . 
RUN pip install --upgrade pip
RUN pip install --upgrade apache-airflow==${AIRFLOW_VERSION} 
RUN pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt

# === influxDB CLI setup
RUN influx config create --config-name imars_config \
    --host-url "${INFLUXDB_HOSTNAME}:8086" \
    --org "imars" \
    --token "${INFLUXDB_TOKEN}" \
    --active


