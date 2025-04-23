import os
import requests
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# InfluxDB client imports
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='sofar_ingest_dag',
    default_args=default_args,
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=True,
    tags=['sofar'],
) as dag:

    def sofar_ingest(ds, prev_ds, **kwargs):
        raw_url = (
            "https://api.sofarocean.com/fetch/download-sensor-data/"
            f"?spotterId=SPOT-30987C"
            f"&startDate={prev_ds}T00:00Z"
            f"&endDate={ds}T00:00Z"
            f"&processingSources=all"
        )
        headers = {
            "User-Agent":      "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0)"
                               " Gecko/20100101 Firefox/113.0",
            "Accept":          "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type":    "application/x-www-form-urlencoded",
            "view_token":      "1bc9848d3e524c34a1eb220e121d9a9e",
            "Sec-Fetch-Dest":  "empty",
            "Sec-Fetch-Mode":  "cors",
            "Sec-Fetch-Site":  "same-site",
            "Pragma":          "no-cache",
            "Cache-Control":   "no-cache",
            "referrer":        "https://spotters.sofarocean.com/",  # lowercase key
            "credentials":     "omit",
            "mode":            "cors",
            # Note: no Accept-Encoding override here
        }

        resp = requests.get(raw_url, headers=headers, timeout=60)
        print("▶ Request URL:     ", resp.url)
        print("▶ Request headers:", resp.request.headers)
        print("▶ Resp status:    ", resp.status_code)
        print("▶ Resp headers:   ", resp.headers)
        print("▶ Content length: ", len(resp.content))
        print("▶ Preview bytes:  ", resp.content[:200])
        resp.raise_for_status()
        # --- Step 2: Load into pandas DataFrame ---
        df = pd.read_csv(StringIO(resp.text))
        print(df.head())

        # Ensure timestamp column is datetime
        df['utc_timestamp'] = pd.to_datetime(df['utc_timestamp'])

        # --- Step 3: Write directly to InfluxDB ---
        token = os.environ["INFLUXDB_TOKEN"]
        url   = os.environ["INFLUXDB_HOSTNAME"]
        org   = "imars"
        bucket = "imars_bucket"

        client = InfluxDBClient(url=url, token=token, org=org)
        write_api = client.write_api(write_options=SYNCHRONOUS)

        points = []
        for _, row in df.iterrows():
            p = (
                Point("sofar_buoy")
                .tag("spotter_id",      "SPOT-30987C")
                .tag("sensor_position", str(row['sensor_position']))
                .time(row["utc_timestamp"])
                # assume data_type column is sofar_temperature for all rows
                .field("sofar_temperature", float(row["value"]))
            )
            points.append(p)

        write_api.write(bucket=bucket, org=org, record=points)
        print(f"{len(points)} points written to InfluxDB")

        client.__del__()  # ensure clean shutdown

    ingest_task = PythonOperator(
        task_id='sofar_ingest',
        python_callable=sofar_ingest,
    )
