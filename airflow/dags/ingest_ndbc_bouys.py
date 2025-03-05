# ingest_ndbc.py
"""
Ingests NDBC timeseries .csv.

mermaid diagram:
NDBC --> SECOORA ERDDAP
  -- "dotis bash cronjob" --> "imars gbucket"
  -- "airflow ingest_ndbc_buoys" --> influxDB
"""
import os
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

from csv2influx import csv2influx

# Define meteorological parameters used in the standard meteorology CSVs.
MET_PARAMS = [
    'air_pressure_at_mean_sea_level', 'air_temperature',
    'sea_surface_temperature', 'wind_speed',
    'wind_from_direction', 'wind_speed_of_gust',
    'sea_surface_wave_significant_height',
    'sea_surface_wave_mean_period',
    'sea_surface_wave_from_direction',
    'sea_surface_wave_period_at_variance_spectral_density_maximum'
]

# Define a data structure similar to the satellite ingestion file.
NDBC_DB_FILES = {
    'FKNMS': {
        'stations': [
            "Little_Rabbit_Key",
            "Peterson_Key",
            "Whipray_Basin",
            "Butternut_Key",
            "Bob_Allen_Key"
        ],
        'datasets': {
            'salinity': {
                'filename_template': "{station}_Buoy_WTMP_SAL.csv",
                'measurement': "salinity",
                'fields': [
                    ["sea_water_temperature", "sea_water_temperature"],
                    ["sea_water_practical_salinity", "sea_water_practical_salinity"]
                ],
                'tags': [
                    ['source', 'NDBC']
                ],
                'timeCol': "time",
                'skiprows': [1]  # skip 2nd header row
            }
        }
    },
    'SEUS': {
        'stations': [
            "Grays_Reef",
            "Fernandina",
            "Charleston"
        ],
        'datasets': {
            'meteorology': {
                'filename_template': "{station}_Buoy_STDMET.csv",
                'measurement': "meteorology",
                'fields': [
                    [param, param] for param in MET_PARAMS
                ],
                'tags': [],
                'timeCol': "time",
                'skiprows': [1]  # skip 2nd header row
            }
        }
    }
}

with DAG(
    'ingest_ndbc_buoys',
    catchup=False,  # latest only
    schedule_interval="0 12 * * *",
    max_active_runs=2,
    default_args={
        "start_date": datetime(2020, 1, 1)
    },
) as dag:
    for region, data in NDBC_DB_FILES.items():
        # Set a region-specific bucket URL as in ingest_sat_ts.py.
        GBUCKET_URL_PREFIX = f"https://storage.googleapis.com/{region.lower()}_csv"
        for station in data['stations']:
            for dataset_name, ds in data['datasets'].items():
                # Build the filename from the template.
                DATA_FNAME = ds['filename_template'].format(station=station)
                task_id = f"ingest_{dataset_name}_{station}"
                # Add the dynamic tag for location.
                tags = ds.get('tags', []) + [['location', station]]
                PythonOperator(
                    task_id=task_id,
                    python_callable=csv2influx,
                    op_kwargs={
                        'data_url': f"{GBUCKET_URL_PREFIX}/{DATA_FNAME}",
                        'measurement': ds['measurement'],
                        'fields': ds['fields'],
                        'tags': tags,
                        'timeCol': ds['timeCol'],
                        'skiprows': ds.get('skiprows', [])
                    },
                )
