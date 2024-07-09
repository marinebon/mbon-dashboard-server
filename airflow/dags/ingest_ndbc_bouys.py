"""
Ingests NERR BUOY timeseries .csv.

```mermaid
NDBC --> SECOORA ERDDAP
  -- "dotis bash cronjob" --> "imars gbucket"
  -- "airflow ingest_nerrs_buoys" --> influxDB
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
    'ingest_ndbc_buoys',
    catchup=False,  # latest only
    schedule_interval="0 0 * * *",
    max_active_runs=2,
    default_args={
        "start_date": datetime(2020, 1, 1)
    },
) as dag:
    SAL_BUOYS = [
        "Little_Rabbit_Key",
        "Peterson_Key",
        "Whipray_Basin",
        "Butternut_Key",
        "Bob_Allen_Key"
    ]

    for buoy_name in SAL_BUOYS:
        # example path: Little_Rabbit_Key_Buoy_WTMP_SAL.csv
        DATA_FNAME = f"{buoy_name}_Buoy_WTMP_SAL.csv"
        PythonOperator(
            task_id=f"ingest_sal_{buoy_name}",
            python_callable=csv2influx,
            op_kwargs={
                'data_url': f"{GBUCKET_URL_PREFIX}/{DATA_FNAME}",
                'measurement': "value",
                'fields': [
                    ["sea_water_temperature", "sea_water_temperature"],
                    ["sea_water_practical_salinity", "sea_water_practical_salinity"]
                ],
                'tags': [
                    ['location', buoy_name]
                ],
                'timeCol': "time"
            },
        )


    MET_BUOYS = [
        "Grays_Reef",
        "Fernandina_Reef",
        "Charleston"
    ]


    for buoy_name in MET_BUOYS:
        # example path: Little_Rabbit_Key_Buoy_WTMP_SAL.csv                                                                      
        DATA_FNAME = f"{buoy_name}_Buoy_STDMET.csv"
        PythonOperator(
            task_id=f"ingest_stdmet_{buoy_name}",
            python_callable=csv2influx,
            op_kwargs={
                'data_url': f"{GBUCKET_URL_PREFIX}/{DATA_FNAME}",
                'measurement': "value",
                'fields': [
                    ["TODO", "TODO"]
                ],
                'tags': [
                    ['location', buoy_name]
                ],
                'timeCol': "time"
            },
        )