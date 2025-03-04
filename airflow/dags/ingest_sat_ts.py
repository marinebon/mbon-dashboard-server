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
    # ========================================================================
    # Satellite RoI Extractions
    # ========================================================================
    SAT_DB_FILES = {
        'SEUS': {
            'stations': [
                '01', '02', '03', '04', '05', '06', '07', '08',
                '09', '10', '11', '12', '13', '14', '15', '16', '17', 'grnms'
            ],
            'variables': {
                'VSNPP': ['Kd_490', 'Rrs_671', 'chlor_a', 'sstn']
            }
        },
        'FKNMS': {
            'stations': [
                'BIS', 'UK', 'MUK', 'MK', 'LK', 'DT', 'MQ',
                'FKNMS', 'SR', 'WFS','EFB', 'WFB',
            ],
            'variables': {
                'MODA': ['chlor_a', 'Rrs_667', 'Kd_490', 'sst4', 'ABI']
            }
        },
        
        # NOTE: which dash are these for?:
        'GOM': {
            'stations': [
                'BIS', 'UK', 'MUK', 'MK', 'LK', 'DT', 'MQ',
                'FKNMS', 'SR', 'WFS', 'EFB', 'WFB'
            ],
            'variables': {
                'VSNPP': ['Kd_490', 'Rrs_671', 'chlor_a', 'sstn']
            }
        }
    }
    
    for region, data in SAT_DB_FILES.items():
        GBUCKET_URL_PREFIX = f"https://storage.googleapis.com/{region.lower()}_csv"
        # Loop through each station in the region
        for roi in data['stations']:
            # Loop through each satellite and variable in the region
            for sat, variables in data['variables'].items():
                for variable in variables:
                    # example path: `SEUS_Kd_490_TS_VSNPP_daily_01.csv`
                    DATA_FNAME = f"{region}_{variable}_TS_{sat}_daily_{roi}.csv"
                    PythonOperator(
                        task_id=f"{region}_{roi}_{sat}_{variable}",
                        python_callable=csv2influx,
                        op_kwargs={
                            'data_url': f"{GBUCKET_URL_PREFIX}/{DATA_FNAME}",
                            'measurement': variable,
                            'fields': [
                                ["mean", "mean"],
                                ["climatology", "climatology"],
                                ["anomaly", "anomaly"]
                            ],
                            'tags': [
                                ['satellite', sat],
                                ['location', roi],
                                ['source', "USF_IMaRS"],
                                ['region', region],
                            ],
                            'timeCol': "Time"
                        },
                    )
