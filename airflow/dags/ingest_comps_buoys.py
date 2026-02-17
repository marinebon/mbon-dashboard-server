"""
Airflow DAG for Marine Data Ingestion
Ingests data from COMPS marine endpoint into InfluxDB
Runs daily at 6pm US Eastern Time

Example URL
```
https://comps.marine.usf.edu:81/services/download.php?
    time=2026-02-10T00:00:00-05:00/2026-02-17T23:59:59-05:00&
    tz=utc&
    standard=true&
    output=text&
    pretty=true&
    parameters[]=C23+Air+temperature&
    parameters[]=C24+Air+temperature&
    parameters[]=C24+Air+pressure
```
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os

# Add the dags directory to the path so we can import helper modules
# Assuming helpers are in the same directory as this DAG file
dag_dir = os.path.dirname(os.path.abspath(__file__))
if dag_dir not in sys.path:
    sys.path.append(dag_dir)

from csv2influx import csv2influx

# Marine data endpoint configuration
BASE_ENDPOINT = "https://comps.marine.usf.edu:81/services/download.php"

# Default args for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=30),
}


def ingest_comps_buoy_data(**context):
    """
    Fetch CSV data from the marine endpoint for the previous day and load to InfluxDB
    using the csv2influx helper.
    """
    execution_date = context['execution_date']
    
    # Get yesterday's date range (full day)
    start_date = (execution_date - timedelta(days=1)).replace(
        hour=22, minute=0, second=0, microsecond=0
    )
    end_date = execution_date.replace(hour=23, minute=0, second=0)
    
    # Format dates for the API (ISO format with timezone)
    start_str = start_date.strftime('%Y-%m-%dT%H:%M:%S-05:00')
    end_str = end_date.strftime('%Y-%m-%dT%H:%M:%S-05:00')
    
    # Construct the full URL manually to match helper expectations
    # Note: requests.get params encoding might differ slightly but csv2influx takes a URL string or file path
    # We will construct a URL string with params encoded.
    
    # Parameters for the query
    params = {
        'time': f'{start_str}/{end_str}',
        'tz': 'utc',
        'standard': 'true',
        'output': 'csv',
        'pretty': 'true',
        'parameters[]': 'C24_INWATER Water Temperature (1 m)'
    }
    
    # Use requests to build the query string correctly
    import requests
    import tempfile
    
    # 1. Get raw content
    # requests.get params encoding might differ slightly but csv2influx takes a URL string or file path
    # We will construct a URL string with params encoded.
    
    req = requests.Request('GET', BASE_ENDPOINT, params=params)
    prepped = req.prepare()
    full_url = prepped.url
    
    print(f"Ingesting data from: {full_url}")
    
    response = requests.get(full_url)
    response.raise_for_status() # Check for HTTP errors

    # 2. Filter out comments (lines starting with %)
    # splitting by lines and filtering
    lines = response.text.splitlines()
    filtered_lines = [line for line in lines if not line.strip().startswith('%')]
    
    print(f"Original line count: {len(lines)}")
    print(f"Filtered line count: {len(filtered_lines)}")

    # 3. Write to a temporary file
    # We use delete=False so we can close it and let csv2influx read it by name
    # We must remember to remove it afterwards
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
        tmp_file.write('\n'.join(filtered_lines))
        tmp_file_path = tmp_file.name
        
    print(f"Saved filtered CSV to: {tmp_file_path}")
    print(f"Head of filtered CSV: {filtered_lines[:5]}") # print first 5 lines for check

    try:
        # 4. Call the helper function with the temporary file
        csv2influx(
            data_url=tmp_file_path,
            measurement='water_temperature',
            tags=[
                ['station', 'C24_INWATER'],
                ['parameter', 'water_temperature'],
                ['depth', '1m']
            ],
            fields=[
                ['C24_INWATER Water Temperature (1 m)', 'value']
            ],
            timeCol='Time (utc)',
            should_convert_time=True
        )
    finally:
        # 5. Cleanup
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
            print(f"Removed temporary file: {tmp_file_path}")

# Define the DAG
with DAG(
    'ingest_comps_buoys',
    default_args=default_args,
    description='Ingest marine water temperature data into InfluxDB daily',
    schedule_interval='0 23 * * *',  # 6pm EST daily (cron uses UTC)
    start_date=datetime(2026, 2, 1, tzinfo=None),
    catchup=False,
    tags=['marine', 'influxdb', 'data-ingestion'],
) as dag:
    
    dag.doc_md = """
    ## Marine Data Ingestion DAG
    
    This DAG fetches water temperature data from the COMPS marine data service
    and loads it into InfluxDB for storage and analysis.
    
    **Schedule**: Daily at 6pm US Eastern Time
    
    **Tasks**:
    1. `ingest_data`: Retrieves CSV data and loads to InfluxDB using `csv2influx` helper.
    """
    
    ingest_task = PythonOperator(
        task_id='ingest_data',
        python_callable=ingest_comps_buoy_data,
        provide_context=True,
    )

