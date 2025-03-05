# sofar_ingest.py
"""
Ingest bouy data from the SOFAR API into InfluxDB.
"""
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

from csv2influx import csv2influx

# =================================================================
# === custom function for submitting headers for SOFAR
# =================================================================
import subprocess
import tempfile

def fetch_csv_with_headers(url):
    # Create a temporary file to store the CSV data.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
        temp_file_path = temp_file.name

    # Build the curl command as a single string, wrapping each argument with single quotes.
    curl_command = (
        f" curl '{url}' "
        " -X GET "
        " -H 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0' "
        " -H 'Accept: application/json, text/plain, */*' "
        " -H 'Accept-Language: en-US,en;q=0.5' "
        " -H 'Content-Type: application/x-www-form-urlencoded' "
        " -H 'view_token: 1bc9848d3e524c34a1eb220e121d9a9e' "
        " -H 'Sec-Fetch-Dest: empty' "
        " -H 'Sec-Fetch-Mode: cors' "
        " -H 'Sec-Fetch-Site: same-site' "
        " -H 'Pragma: no-cache' "
        " -H 'Cache-Control: no-cache' "
        " -H 'referrer: https://spotters.sofarocean.com/' "
        " -H 'credentials: omit' "
        " -H 'mode: cors' "
        f" > {temp_file_path}"
    )

    result = subprocess.run(curl_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        error_msg = result.stderr.decode('utf-8')
        raise Exception(f"Curl command failed with error: {error_msg}")

    return temp_file_path
# =================================================================
with DAG(
    'sofar_ingest',
    catchup=True,
    schedule_interval="0 0 * * *",
    max_active_runs=4,
    default_args={
        "start_date": datetime(2023, 6, 20),
        'retries': 3,
        'retry_delay': timedelta(days=1),
    },
) as dag:
    PythonOperator(
        task_id="sofar_ingest",
        python_callable=csv2influx,
        op_kwargs={
            # Templated URL using Airflow's Jinja to substitute previous and current execution dates.
            'data_url': (
                "https://api.sofarocean.com/fetch/download-sensor-data/"
                "?spotterId=SPOT-30987C"
                "&startDate={{ prev_ds }}T00:00Z"
                "&endDate={{ ds }}T00:00Z"
                "&processingSources=all"
            ),
            'data_fetcher_fn': fetch_csv_with_headers,
            'measurement': "sofar_bouy",
            'fields': [
                ["value", "value"],
                ["sensor_position", "sensor_position"]
            ],
            'tags': [
                ['spotter_id', 'SPOT30987C'],
                ['source', 'sofar']
            ],
            'timeCol': "utc_timestamp",
            'should_convert_time': True,
        },
    )
