"""
Ingests OA data for GRNMS.
"""
import os

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime

REGION = 'SEUS'
DATA_HOST = "https://storage.googleapis.com/dashboards_csvs"

REGION_UPPERCASE = REGION.upper()  # bc cannot do REGION.upper() inside f string.
# ============================================================================
# === DAG defines the task exec order
# ============================================================================
with DAG(
    'ingest_oa',
    catchup=False,  # latest only
    schedule_interval="@once",  # run only once (unless triggered manually)
    max_active_runs=1,
    default_args={
        "start_date": datetime(2023, 1, 1)
    },
) as dag:
    UPLOADER_HOSTNAME = os.environ["UPLOADER_HOSTNAME"]
    if UPLOADER_HOSTNAME.endswith('/'):  # rm possible trailing /
        UPLOADER_HOSTNAME = UPLOADER_HOSTNAME[:-1]
    UPLOADER_ROUTE = UPLOADER_HOSTNAME + "/submit/sat_image_extraction"
  
    PARAM_LIST = {
        'ApCo2': 'pco2_in_air',
        'Sal': 'sea_water_practical_salinity',
        'WTemp': 'sea_water_temperature',
        'WpCo2': 'pco2_in_sea_water',
        'pH': 'sea_water_ph_reported_on_total_scale',
    }
    FPATH = "gov_ornl_cdiac_graysrf_{param_name}.csv "
    for param_name, param_col_name in PARAM_LIST.items():
        BashOperator(
            task_id=f"ingest_oa_{param_name}",
            bash_command=(
                "curl --fail-with-body "
                "    {{params.DATA_HOST}}/{{params.fpath}} "
                "    > datafile.csv" 
                " && sed -i '2d' datafile.csv "   # drop 2nd row of the csv file (this is the units row)
                " && curl --fail-with-body "
                '    --form measurement=oa_params '
                '    --form fields={{params.col_name}} '
                '    --form time_column=time '
                '    --form file=@./datafile.csv '
                '    {{params.uploader_route}} '
            ),
            params={
                "uploader_route": UPLOADER_ROUTE,
                "fpath": FPATH.format(**vars()),
                "DATA_HOST": DATA_HOST,
                "col_name": param_col_name,
            }
        )
    
