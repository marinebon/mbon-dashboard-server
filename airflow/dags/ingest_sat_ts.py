"""
Ingests all timeseries .csv.

```mermaid
NASA subscription
  -- "dotis cron" --> imars_netcdfs 
  -- "dotis matlab cron" --> "anom+clim csv files"
  -- "dotis cron" --> gbucket
  -- "airflow ingest_sat_ts" --> influxDB
```
"""
import os

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

from csv2influx import csv2influx

REGION = 'SEUS'
DATA_HOST = "https://storage.googleapis.com/dashboards_csvs"

REGION_UPPERCASE = REGION.upper()  # bc cannot do REGION.upper() inside f string.
# ============================================================================
# === DAG defines the task exec order
# ============================================================================
with DAG(
    'ingest_sat_ts',
    catchup=False,  # latest only
    schedule_interval="0 12 * * *",
    max_active_runs=1,
    default_args={
        "start_date": datetime(2020, 1, 1)
    },
) as dag:
    GBUCKET_URL_PREFIX = "https://storage.googleapis.com/dashboards_csvs"
    # ========================================================================
    # Satellite RoI Extractions
    # ========================================================================
    SAT_ROI_LIST = [
        '01', '02', '03', '04', '05', '06', '07', '08', '09',
        '10', '11', '12', '13', '14', '15', '16', '17','grnms'
    ]
    SAT_FILE_DETAIL_LIST = [
        # sat    | product
        ['VSNPP', 'Kd_490'],
        ['VSNPP', 'Rrs_671'],
        ['VSNPP', 'chlor_a'],
        ['VSNPP', 'sstn'],
        #["MODA", "chlor_a"],
        #["MODA", "Rrs_667"],
        #["MODA", "Kd_490"],
        #["MODA", "sst4"],
        #["MODA",  "ABI"],
    ]
    for roi in SAT_ROI_LIST:
        for sat, product in SAT_FILE_DETAIL_LIST:
            # example path: `SEUS_Kd_490_TS_VSNPP_daily_01.csv`
            DATA_FNAME = f"{REGION}_{product}_TS_{sat}_daily_{roi}.csv"
            PythonOperator(
                task_id=f"ingest_sat_{roi}_{sat}_{product}",
                python_callable=csv2influx,
                op_kwargs={
                    'data_url': f"{GBUCKET_URL_PREFIX}/{DATA_FNAME}",
                    'measurement': product,
                    'fields': [
                        ["mean", "mean"],
                        ["climatology", "climatology"],
                        ["anomaly", "anomaly"]
                    ],
                    'tags': [
                        ['satellite', sat],
                        ['location', roi],
                        ['source', "USF_IMaRS"]
                    ],
                    'timeCol': "Time"
                },
            )
