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
import pycurl
import tempfile
import certifi

def fetch_csv_with_headers(url):
    # Create a temporary file to store the CSV data.
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    temp_file_path = temp_file.name
    temp_file.close()  # We'll let pycurl write to the file.

    # List of headers matching the original working curl command.
    headers = [
        "User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0",
        "Accept: application/json, text/plain, */*",
        "Accept-Language: en-US,en;q=0.5",
        "Content-Type: application/x-www-form-urlencoded",
        "view_token: 1bc9848d3e524c34a1eb220e121d9a9e",
        "Sec-Fetch-Dest: empty",
        "Sec-Fetch-Mode: cors",
        "Sec-Fetch-Site: same-site",
        "Pragma: no-cache",
        "Cache-Control: no-cache",
        "referrer: https://spotters.sofarocean.com/",
        "credentials: omit",
        "mode: cors",
        "Origin: https://spotters.sofarocean.com"
    ]

    # Initialize a pycurl object.
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.HTTPHEADER, headers)
    # Ensure that certificate verification works.
    c.setopt(c.CAINFO, certifi.where())
    # Write the output to our temporary file.
    with open(temp_file_path, 'wb') as f:
        c.setopt(c.WRITEDATA, f)
        c.perform()
    # Check HTTP response code.
    http_code = c.getinfo(c.RESPONSE_CODE)
    c.close()
    
    if http_code not in (200, 304):
        raise Exception(f"HTTP request failed with status code {http_code}")
    
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
