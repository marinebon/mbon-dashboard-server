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
    output=csv&
    pretty=true&
    parameters[]=C23+Air+temperature&
    parameters[]=C24+Air+temperature&
    parameters[]=C24+Air+pressure&
    parameters[]=C24_INWATER+Water+Temperature+(1+m)
```


SELECT "C24_INWATER Water Temperature (deg C) (1 m)"
FROM "water_temperature"
WHERE "station" = 'C24_INWATER' AND $timeFilter
"""

# TODO: update river discharge queries & buoys in grafana dashboard
#       + dropdown for river discharge

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

from dataframe_to_influx import dataframe_to_influx


INGEST_HOUR_UTC = 23  # 6pm EST

# Marine data endpoint configuration
BASE_ENDPOINT = "https://comps.marine.usf.edu:81/services/download.php"

# Default args for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(days=10),
}


def ingest_comps_buoy_data(station, parameters, **context):
    """
    Fetch CSV data from the marine endpoint for the previous day and load to InfluxDB
    """
    execution_date = context['execution_date']
    
    # Get yesterday's date range (full day with 1 hour overlap)
    start_date = (execution_date - timedelta(days=1)).replace(
        hour=INGEST_HOUR_UTC-5-1,  # convert to EST and allow one hour of overlap
        minute=0, 
        second=0, 
        microsecond=0
    )
    end_date = execution_date.replace(
        hour=INGEST_HOUR_UTC-5,  # convert to EST
        minute=0, 
        second=0
    )
    
    # Format dates for the API (ISO format with timezone)
    start_str = start_date.strftime('%Y-%m-%dT%H:%M:%S-05:00')
    end_str = end_date.strftime('%Y-%m-%dT%H:%M:%S-05:00')
    
    # Parameters for the query
    params = {
        'time': f'{start_str}/{end_str}',
        'tz': 'utc',
        'standard': 'true',
        'output': 'csv',
        'pretty': 'true',
        'parameters[]': parameters
    }
    
    import requests
    import tempfile

    # === Get raw content    
    req = requests.Request('GET', BASE_ENDPOINT, params=params)
    prepped = req.prepare()
    full_url = prepped.url
    
    print(f"Ingesting data from: {full_url}")
    
    response = requests.get(full_url)
    response.raise_for_status() # Check for HTTP errors


    # === Filter out comments (lines starting with %)
    lines = response.text.splitlines()
    filtered_lines = [line for line in lines if not line.strip().startswith('%')]
    
    print(f"Original line count: {len(lines)}")
    print(f"Filtered line count: {len(filtered_lines)}")

    
    # === convert to dataframe
    import pandas as pd
    import io
    df = pd.read_csv(io.StringIO('\n'.join(filtered_lines)))
    print(df.head())


    # === Read column names in directly from the file
    time_col = 'Time (utc)'
    dynamic_fields = [
        [col, col] for col in df.columns 
        if (
            col and 
            col != time_col and 
            not col.endswith(' quality')
        )
    ]
    print(f"dynamic fields: {dynamic_fields}")

    # === Filter out data with quality != "good"
    n_filtered_values = 0
    for col in df.columns:
        if col.endswith(' quality'):
            col_to_filter = col.replace(' quality', '')
            # set value to NaN if quality != "good"
            df.loc[df[col] != 'good', col_to_filter] = pd.NA
            n_filtered_values += df[col].value_counts()['good']
    
    # drop quality columns
    df = df.drop(columns=[col for col in df.columns if col.endswith(' quality')])

    print(f'{n_filtered_values} values removed because quality != "good"')

    # === Call the helper function with the temporary file
    dataframe_to_influx(
        dataframe=df,
        measurement='comps_buoy',  # changed from water_temperature
        tags=[
            ['station', station]
        ],
        fields=dynamic_fields,
        timeCol='Time (utc)',
        should_convert_time=True
    )


with DAG(
    'ingest_comps_buoys',
    default_args=default_args,
    description='Ingest marine water temperature data into InfluxDB daily',
    schedule_interval=f'0 {INGEST_HOUR_UTC} * * *',
    start_date=datetime(2025, 10, 27, tzinfo=None),  # first day of buoy data
    catchup=True,
    tags=['marine', 'influxdb', 'data-ingestion'],
) as dag:
    
    dag.doc_md = """
    ## Marine Data Ingestion DAG
    
    This DAG fetches water temperature data from the COMPS marine data service
    and loads it into InfluxDB.
    """
    
    ingest_c23_task = PythonOperator(
        task_id='ingest_c23_data',
        python_callable=ingest_comps_buoy_data,
        provide_context=True,
        op_kwargs={
            'station': 'C23',
            'parameters': ['C23 Air temperature']
        }
    )

    ingest_c24_task = PythonOperator(
        task_id='ingest_c24_data',
        python_callable=ingest_comps_buoy_data,
        provide_context=True,
        op_kwargs={
            'station': 'C24',
            'parameters': [
                'C24 Air temperature',
                'C24 Air pressure',
                'C24_INWATER Water Temperature (1 m)'
            ]
        }
    )
