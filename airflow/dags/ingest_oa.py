"""
Ingests OA data for GRNMS.
"""
import os

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

from csv2influx import csv2influx

DATA_HOST = "https://storage.googleapis.com/dashboards_csvs"

# ============================================================================
# === DAG defines the task exec order
# ============================================================================
with DAG(
    'ingest_oa',
    catchup=False,  # latest only
    schedule_interval="@once",  # run only once (unless triggered manually)
    max_active_runs=2,
    default_args={
        "start_date": datetime(2023, 1, 1)
    },
) as dag:
    PARAM_LIST = {
        'ApCo2': 'pco2_in_air',
        'Sal': 'sea_water_practical_salinity',
        'WTemp': 'sea_water_temperature',
        'WpCo2': 'pco2_in_sea_water',
        'pH': 'sea_water_ph_reported_on_total_scale',
    }
    FPATH = "gov_ornl_cdiac_graysrf_{param_name}.csv "
    for param_name, param_col_name in PARAM_LIST.items():

        PythonOperator(
            task_id=f"ingest_oa_{param_name}",
            python_callable=csv2influx,
            op_kwargs={
                'data_url': f"{{DATA_HOST}}/{{FPATH}}",
                'measurment': 'oa_params',
                'fields': [
                    [param_name, param_col_name]
                ],
                'tags': [],
                'timeCol':'time'
            }
        )
        
    
