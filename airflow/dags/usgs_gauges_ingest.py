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

discharge_metadata = {
    'filename_template': "USGS_disch_{REGION}db_{location}.csv",
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
gh_metadata = {
    'filename_template': "USGS_gh_{location}_{REGION}db.csv",
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

USGS_DB_FILES = {
    'SEUS': {
        'locations': [
            'SavannahRv', 'HudsonCr', 'AltamahaRv', 'SatillaRv',
            'StJohnsRv', 'OgeecheeRv', 'BrunswickRv', 'StMarysRv'
        ],
        'datasets': {
            'gh': gh_metadata
        }
    },
    'FWC': {
        'locations': [
          'EFL', 'STL'
        ],
        'datasets': {
            'disch': discharge_metadata
        }
    },
    'FK': {
        'locations': [
          ''  # NOTE: this location has no name?
        ],
        'datasets': {
            'disch': discharge_metadata
        }
    },
    'FGB': {
        'locations': [
            'MS', 'TX', 
        ],
        'datasets': {
            'disch': discharge_metadata
        }
    },
    'REACH': {
        'locations': [
            'AlabamaRv','ApalachicolaRv','ChoctawRv','EscambiaRv',
            'PascagoulaRv','PearlRv','SuwanneeRv','TombigbeeRv'
        ],
        'datasets': {
            'disch': discharge_metadata
        }
    }
}

with DAG(
    'usgs_gauges_ingest',
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
        # set region for URL 
        if region in ['FK', 'FWC', 'FGB', 'REACH']:
            gbucket_name = 'GOM'
        elif region == "SEUS":
            gbucket_name = 'SEUS'
        else:
            raise ValueError(f"unexpected region: '{region}'")
        # Use the region in the URL generation.
        GBUCKET_URL_PREFIX = f"https://storage.googleapis.com/{gbucket_name.lower()}_csv"
        for dataset_name, ds in region_data['datasets'].items():
            for location in region_data['locations']:
                DATA_FNAME = ds['filename_template'].format(
                  location=location,
                  REGION=region
                )
                # handle special case of missing location (FK)
                if location == '':
                  # drop the _ before .csv
                  DATA_FNAME = DATA_FNAME[:-5] + '.csv'
                  location = 'fk'
                task_id = f"{region}_{dataset_name}_{location}"
                tags = ds.get('tags', []) + [
                    ['location', location],
                    ['region', region]
                ]
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
