# ingest_usgs_gauges.py
"""
Ingest of USGS discharge and gauge height data.

mermaid:
usgs 
  -- ??? --> gbucket 
  -- "airflow ingest_USGS_gauges" --> influxDB
"""
import os
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

from csv2influx import csv2influx

USGS_DB_FILES = {
    'SEUS': {
        'locations': [
            'SavannahRv_SEUSdb', 'HudsonCr_SEUSdb', 'AltamahaRv_SEUSdb', 'SatillaRv_SEUSdb',
            'StJohnsRv_SEUSdb', 'OgeecheeRv_SEUSdb', 'BrunswickRv_SEUSdb', 'StMarysRv_SEUSdb'
        ],
        'datasets': {
            'gh': {
                'filename_template': "USGS_gh_{location}.csv",
                'measurement': "gh",
                'fields': [
                    ["mean", "mean"],
                    ["climatology", "climatology"],
                    ["anomaly", "anomaly"]
                ],
                'tags': [
                    ['parameter', 'gh'],
                    ['source', 'USGS']
                ],
                'timeCol': "time"
            }
        }
    },
    'FGB': {
        'locations': [
            'FGBdb_MS', 'FGBdb_TX', 'FKdb', 'FWCdb_EFL', 'FWCdb_STL'
        ],
        'datasets': {
            'disch': {
                'filename_template': "USGS_disch_{location}.csv",
                'measurement': "disch",
                'fields': [
                    ["mean", "mean"],
                    ["climatology", "climatology"],
                    ["anomaly", "anomaly"]
                ],
                'tags': [
                    ['parameter', 'disch'],
                    ['source', 'USGS']
                ],
                'timeCol': "time"
            }
        }
    }
}

with DAG(
    'ingest_usgs_gauges',
    catchup=False,
    schedule_interval="0 12 * * *",
    max_active_runs=2,
    default_args={
        "start_date": datetime(2023, 6, 20),
        # 'retries': 3,
        # 'retry_delay': timedelta(days=1),
    },
) as dag:
    for region, region_data in USGS_DB_FILES.items():
        # Use the region in the URL generation.
        GBUCKET_URL_PREFIX = f"https://storage.googleapis.com/{region.lower()}_csv"
        for dataset_name, ds in region_data['datasets'].items():
            for location in region_data['locations']:
                DATA_FNAME = ds['filename_template'].format(location=location)
                task_id = f"{region}_{dataset_name}_{location}"
                tags = ds.get('tags', []) + [['location', location]]
                PythonOperator(
                    task_id=task_id,
                    python_callable=csv2influx,
                    op_kwargs={
                        'data_url': f"{GBUCKET_URL_PREFIX}/{DATA_FNAME}",
                        'measurement': ds['measurement'],
                        'fields': ds['fields'],
                        'tags': tags,
                        'timeCol': ds['timeCol']
                    },
                )
