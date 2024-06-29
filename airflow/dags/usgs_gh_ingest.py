"""
Ingest of USGS discharge and guage height data.
"""
import os

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

# These jobs run once to grab all the data.
# TODO: modify to only grab latest data.
with DAG(
    'nerr_data_ingest',
    catchup=False,
    schedule_interval="0 0 * * *",
    max_active_runs=1,
    default_args={
        "start_date": datetime(2023, 6, 20),
        #'retries': 3,
        #'retry_delay': timedelta(days=1),
    },
) as dag:
    def data2influx(data_url, measurement, tags=[], field=["value", "Sal"], timeCol='DateTimeStamp'):
        """
        fetch data from IMaRS gcloud bucket
        """
        import pandas as pd
        try: 
            data = pd.read_csv(data_url)
            print(f"loaded data cols: {data.columns}")
            print(f"1st few rows:\n {data.head()}")
        except Exception as e:
            print(f"failed to `getData({data_url})`...\n", e)
            raise e
        
        # === upload the data
        # influx connection setup
        import influxdb_client, os, time
        from influxdb_client import InfluxDBClient, Point, WritePrecision
        from influxdb_client.client.write_api import SYNCHRONOUS
        
        token = os.environ.get("INFLUXDB_TOKEN")
        org = "imars"
        url = os.environ.get("INFLUXDB_HOSTNAME")
        
        client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
        bucket="imars_bucket"
        
        # write each point in the df to influxDB
        points = []
        for index, row in data.iterrows():
            print(f"{row['Sal']} @ {row['DateTimeStamp']}")
            point = (
                Point(measurement)
                .time(row[timeCol])  # not utc_timestamp ?
            )
            for key, val in fields:
                point = point.field(key, row[val])
            for key, val in tags:
                point = point.tag(key, val)
            points.append(point)
        
        # Batch write points
        results = client.write_api(write_options=SYNCHRONOUS).write(bucket=bucket, org=org, record=points)  
        # Manually close the client to ensure no batching issues
        client.__del__()
        print("influxdb API response:")
        print(results)

    GBUCKET_URL_PREFIX = "https://storage.googleapis.com/dashboards_csvs"
    FILE_LIST = {
        'gh': [
            'SavannahRv_SEUSdb','HudsonCr_SEUSdb_SEUSdb','AltamahaRv_SEUSdb','SatillaRv_SEUSdb',
            'StJohnsRv_SEUSdb','OgeecheeRv_SEUSdb','BrunswickRv_SEUSdb','StMarysRv_SEUSdb'
        ],
        'disch': [
            'FGBdb_MS', 'FGBdb_TX',
            'FKdb',
            'FWCdb_EFL', 'FWCdb_STL'
        ]
    }
    # example fname: USGS_gh_SavannahRv_SEUSdb.csv
    for param, locations in FILE_LIST.items():
        for location in locations:
            DATA_FNAME = f"USGS_{param}_{location}.csv"
            PythonOperator(
                task_id=f"ingest_usgs_{param}_{location}",
                python_callable=data2influx,
                op_kwargs={
                    'data_url': f"{GBUCKET_URL_PREFIX}/{DATA_FNAME}",
                    'measurement': param,
                    'fields': [
                        ["mean", "mean"],
                        ["climatology", "climatology"],
                        ["anomaly", "anomaly"]
                    ],
                    'tags': [
                        ['parameter', param],
                        ['location', location]
                    ],
                    'timeCol': "time"
                },
            )

