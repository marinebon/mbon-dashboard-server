"""
Ingests NERR BOUY timeseries .csv.

```mermaid
NERRS --> ERDDAP
  -- "dotis bash cronjob" --> "imars gbucket"
  -- "airflow ingest_nerrs_bouys" --> influxDB
```
"""
import os

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

from csv2influx import csv2influx

GBUCKET_URL_PREFIX = "https://storage.googleapis.com/dashboards_csvs"
# ============================================================================
# === DAG defines the task exec order
# ============================================================================
with DAG(
    'ingest_nerrs_bouys',
    catchup=False,  # latest only
    schedule_interval="0 0 * * *",
    max_active_runs=1,
    default_args={
        "start_date": datetime(2020, 1, 1)
    },
) as dag:
    SAL_BOUYS = [
        ["Little_Rabbit_Key", "WTMP_SAL"],
        ["Peterson_Key", "WTMP_SAL"],
        ["Whipray_Basin", "WTMP_SAL"],
        ["Butternut_Key", "WTMP_SAL"],
        ["Bob_Allen_Key", "WTMP_SAL"]
    ]

    for bouy_name in SAL_BOUYS:
        # example path: Little_Rabbit_Key_Buoy_WTMP_SAL.csv
        DATA_FNAME = f"{bouy_name}_Bouy_WTMP_SAL.csv"
        PythonOperator(
            task_id=f"ingest_sal_{bouy_name}",
            python_callable=csv2influx,
            op_kwargs={
                'data_url': f"{GBUCKET_URL_PREFIX}/{DATA_FNAME}",
                'measurement': "value",
                'fields': [
                    ["sea_water_temperature", "sea_water_temperature"],
                    ["sea_water_practical_salinity", "sea_water_practical_salinity"]
                ],
                'tags': [
                    ['location', bouy_name]
                ],
                'timeCol': "time"
            },
        )


    MET_BOUYS = [
        ["Grays_Reef", "STDMET"],
        ["Fernandina_Reef", "STDMET"],
        ["Charleston", "STDMET"]
    ]


    for bouy_name in MET_BOUYS:
        # example path: Little_Rabbit_Key_Buoy_WTMP_SAL.csv                                                                      
        DATA_FNAME = f"{bouy_name}_Bouy_STDMET.csv"
        PythonOperator(
            task_id=f"ingest_stdmet_{bouy_name}",
            python_callable=csv2influx,
            op_kwargs={
                'data_url': f"{GBUCKET_URL_PREFIX}/{DATA_FNAME}",
                'measurement': "value",
                'fields': [
                    ["TODO", "TODO"]
                ],
                'tags': [
                    ['location', bouy_name]
                ],
                'timeCol': "time"
            },
        )
