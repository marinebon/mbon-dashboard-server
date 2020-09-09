"""
Ingests data from FWC argis portal into influxdb using mbon_data_uploader.
"""
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime

DAGS_DIR = "/usr/local/airflow/dags/"


with DAG(
    'coral_disease_from_arcgis',
    catchup=False,  # latest only
    schedule_interval="0 0 * * *",
    max_active_runs=1,
    default_args={
        "start_date": datetime(2020, 1, 1)
    },
) as dag:
    ingest_all = BashOperator(
        task_id='ingest_all',
        bash_command="python " + DAGS_DIR + "coral_disease_from_arcgis.py"
    )
