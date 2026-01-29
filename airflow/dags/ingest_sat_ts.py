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
                'MODA': ['ABI'],
                'VSNPP': ['Kd_490', 'Rrs_671', 'chlor_a', 'sstn']
            }
        },

        # GoM = FKNMS + FGBNMS + FWC
        'FKNMS': {
            'stations': [
                'BIS', 'UK', 'MUK', 'MK', 'LK', 'DT', 'MQ',
                'FKNMS', 'SR', 'WFS','EFB', 'WFB',
            ],
            'variables': {
                'MODA': ['chlor_a', 'Rrs_667', 'Kd_490', 'ABI'],
                'VSNPP': ['Kd_490', 'Rrs_671', 'chlor_a', 'sstn']
            }
        },
        'FGBNMS': {
            'stations': [
              'STET', 'WFG', 'EFG',
              'COAST1', 'COAST2', 'COAST3', 'COAST4', 
              'SS1', 'SS2', 'SS3', 'SS4', 'SS5', 'SS6', 'SS7', 'SS8'
            ],
            'variables': {
                'MODA': ['chlor_a', 'Rrs_667', 'Kd_490', 'ABI'],
                'VSNPP': ['Kd_490', 'Rrs_671', 'chlor_a', 'sstn']
            }
        },
        'FWC': {
          'stations': [
              'SLI', 'PBI', 'PEV', 'MIA', 'MOL', 'SOM', 'SUG', 'KW'
            ],
            'variables': {
                'MODA': ['chlor_a', 'Rrs_667', 'Kd_490', 'ABI'],
                'VSNPP': ['Kd_490', 'Rrs_671', 'chlor_a', 'sstn']
            }
        },
        'REACH': {
            'stations': [
                'REACH_S01', 'REACH_S02', 'REACH_S03', 'REACH_S04', 'REACH_S05',
                'REACH_S06', 'REACH_S07', 'REACH_S08', 'REACH_S09', 'REACH_S10',
                'REACH_S11', 'REACH_S12', 'REACH_S13', 'REACH_S14', 'REACH_S15',
                'REACH_S16', 'REACH_S17', 'REACH_S18', 'REACH_S19', 'REACH_S20',
                'REACH_S21', 'REACH_S22', 'REACH_S23'
            ],
            'variables': {
                'MODA': ['ABI'],
                'VSNPP': ['Kd_490', 'Rrs_671', 'chlor_a', 'sstn']
            }
        }
    }
    
    for region, data in SAT_DB_FILES.items():
        if region in ['FWC', 'FKNMS', 'FGBNMS', 'REACH']:
            gbucket_region = 'GOM'
        else:
            gbucket_region = region
        GBUCKET_URL_PREFIX = f"https://storage.googleapis.com/{gbucket_region.lower()}_csv"
        # Loop through each station in the region
        for roi in data['stations']:
            # Loop through each satellite and variable in the region
            for sat, variables in data['variables'].items():
                for variable in variables:
                    # example path: `SEUS_Kd_490_TS_VSNPP_daily_01.csv`
                    DATA_FNAME = f"{gbucket_region}_{variable}_TS_{sat}_daily_{roi}.csv"
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
