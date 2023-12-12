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
    'ts_ingest',
    catchup=False,  # latest only
    schedule_interval="0 0 0 0 *",  # TODO: set this to only run once or when manually triggered
    max_active_runs=1,
    default_args={
        "start_date": datetime(2020, 1, 1)
    },
) as dag:
    UPLOADER_HOSTNAME = os.environ["UPLOADER_HOSTNAME"]
    if UPLOADER_HOSTNAME.endswith('/'):  # rm possible trailing /
        UPLOADER_HOSTNAME = UPLOADER_HOSTNAME[:-1]
    UPLOADER_ROUTE = UPLOADER_HOSTNAME + "/submit/sat_image_extraction"
  
    PARAM_LIST = ['ApCo2', 'Sal', 'WTemp', 'WpCo2', 'pH']
    FIELDS_LIST = [  # NOTE: These must line up with the PARAMS listed above
      'pco2_in_air', 
      'sea_water_practical_salinity', 
      'sea_water_temperature', 
      'pco2_in_sea_water',
      'sea_water_ph_reported_on_total_scale'
    ]
    FPATH = "gov_ornl_cdiac_graysrf_{param}.csv "
    for river in USGS_RIVER_LIST:
        BashOperator(
            task_id=f"ingest_river_{river}",
            bash_command=(
                "curl --fail-with-body "
                "    {{params.DATA_HOST}}/{{params.fpath}} "
                "    > datafile.csv" 
                " && awk ... > datafile.csv"   # TODO: drop 2nd row of csv file
                " && curl --fail-with-body "
                '    --form measurement=oa_params '
                '    --form fields=mean,climatology,anomaly '  # TODO: use field hree
                '    --form time_column=time '
                '    --form file=@./datafile.csv '
                '    {{params.uploader_route}} '
            ),
            params={
                "river": river,
                "uploader_route": UPLOADER_ROUTE,
                "fpath": FPATH.format(**vars()),
                "DATA_HOST": DATA_HOST
            }
        )
    
