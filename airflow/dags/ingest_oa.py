"""
Ingest Ocean Acidifcation data.


# === Data Sources
## Real Time
SECOORA portal | 2018-present
  https://portal.secoora.org/#metadata/75594/station/data
  Cannot Download(?)


## HISTORIC
SECOORA portal | -2019:
  https://portal.secoora.org/#metadata/49365/station/data
  Cannot Download(?)
ERDDAP         |  -2019:
  https://erddap.secoora.org/erddap/tabledap/gov_ornl_cdiac_graysrf_81w_31n.html
NCEI           | -2020:
  https://www.ncei.noaa.gov/data/oceans/ncei/ocads/data/0109904/
NCEI OCADS     | 2006-2020:
  https://www.ncei.noaa.gov/access/ocean-carbon-acidification-data-system/oceans/Moorings/Grays_Reef.html
"""
import os

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import requests, gzip, io
import pandas as pd

from dataframe_to_influx import dataframe_to_influx


# ============================================================================
# === DAG defines the task exec order
# ============================================================================
with DAG(
    'ingest_oa',
    catchup=True,  # latest only
    schedule_interval="@yearly",
    max_active_runs=2,
    default_args={
        "start_date": datetime(2020, 2, 1)  # 1 month delay for NDBC to publish last year's data
    },
) as dag:

    #YY  MM DD hh mm WDIR WSPD GST  WVHT   DPD   APD MWD   PRES  ATMP  WTMP  DEWP  VIS  TIDE
    PARAM_LIST = {
        'ApCo2': 'pco2_in_air',
        'Sal': 'sea_water_practical_salinity',
        'WTemp': 'sea_water_temperature',
        'WpCo2': 'pco2_in_sea_water',
        'pH': 'sea_water_ph_reported_on_total_scale',
    }
    for param_name, param_col_name in PARAM_LIST.items():
        FPATH = f"gov_ornl_cdiac_graysrf_{param_name}.csv"
        PythonOperator(
            task_id=f"ingest_oa_{param_name}",
            python_callable=ndbc_to_influx,
            provide_context=True,
            op_kwargs={
                'buoy_id': '41008h',
                'measurement': 'oa_params',
                'fields': [
                    [param_col_name, param_name]
                ],
                'skiprows': [1],  # skip 2nd header row (units)
                'tags': ["source", "ORNL_OA"],
                'timeCol':'time'
            }
        )
        
    
