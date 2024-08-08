"""
Ingest of USGS discharge and guage height data.

```mermaid
usgs 
  -- ??? --> gbucket 
  -- "airflow ingest_USGS_guages" --> influxDB
```
"""
import os

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

# These jobs run once to grab all the data.
# TODO: modify to only grab latest data.
with DAG(
    'ingest_usgs_gauges',
    catchup=False,
    schedule_interval="0 12 * * *",
    max_active_runs=2,
    default_args={
        "start_date": datetime(2023, 6, 20),
        #'retries': 3,
        #'retry_delay': timedelta(days=1),
    },
) as dag:
    from csv2influx import csv2influx
    
    GBUCKET_URL_PREFIX = "https://storage.googleapis.com/dashboards_csvs"
    FILE_LIST = {
        'gh': [
            'SavannahRv_SEUSdb','HudsonCr_SEUSdb','AltamahaRv_SEUSdb','SatillaRv_SEUSdb',
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
                python_callable=csv2influx,
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

