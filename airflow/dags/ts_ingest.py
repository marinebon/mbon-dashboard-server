"""
Ingests all timeseries .csv files into influxdb using mbon_data_uploader.

# files linked to 7yl4r's public_html folder on IMaRS servers like so:
[tylar@seashell ~]$ ln -s /srv/imars-objects/fgb/DISCH_CSV_USGS/USGS_disch_FGBdb_TX.csv public_html/fgb-_-DISCH_CSV_USGS-_-USGS_disch_FGBdb_TX.csv
[tylar@seashell ~]$ ln -s /srv/imars-objects/fgb/DISCH_CSV_USGS/USGS_disch_FGBdb_MS.csv public_html/fgb-_-DISCH_CSV_USGS-_-USGS_disch_FGBdb_MS.csv
# note how dir separator (/) is replaced w/ -_-
"""
import os

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime

REGION = 'fk'
DATA_HOST = "http://imars.marine.usf.edu/~tylar"

FNAME_PREFIX = 'FKdbv2'

SAT_ROI_LIST = [
    'WFG', 'EFG', 'STET', 'COAST1', 'COAST2', 'COAST3', 'COAST4', 'SS1',
    'SS2', 'SS3', 'SS4', 'SS5', 'SS6', 'SS7', 'SS8'
]
SAT_FILE_DETAIL_LIST = [
    ["VSNPP", "OC", "chlor_a"],
    ["VSNPP", "OC", "Rrs_671"],
    ["VSNPP", "SSTN", "sstn"],
    ["MODA", "OC", "ABI"],
]

BOUY_ROI_LIST = []

USGS_RIVER_LIST = ['FGBdb_MS', 'FGBdb_TX']


with DAG(
    'ts_ingest',
    catchup=False,  # latest only
    schedule_interval="0 0 * * *",
    max_active_runs=1,
    default_args={
        "start_date": datetime(2020, 1, 1)
    },
) as dag:
    UPLOADER_HOSTNAME = os.environ["UPLOADER_HOSTNAME"]
    if UPLOADER_HOSTNAME.endswith('/'):  # rm possible trailing /
        UPLOADER_HOSTNAME = UPLOADER_HOSTNAME[:-1]
    UPLOADER_ROUTE = UPLOADER_HOSTNAME + "/submit/sat_image_extraction"

    # ========================================================================
    # Satellite RoI Extractions
    # ========================================================================
    for roi in SAT_ROI_LIST:
        for sat, product_type, product in SAT_FILE_DETAIL_LIST:
            fpath = f"{REGION}-_-EXT_TS_{sat}-_-{product_type}-_-{REGION}_{product}_TS_{sat}_daily_{roi}.csv"
            download_task = BashOperator(
                task_id=f"upload_sat_roi_{REGION}_{sat}_{product}_{roi}",
                bash_command=(
                    "curl --fail "
                    "{{params.DATA_HOST}}/{{params.fpath}} "
                ),
                params={
                    "fpath": fpath,
                    "DATA_HOST": DATA_HOST
                }
            )
            upload_task = BashOperator(
                task_id=f"sat_roi_{REGION}_{sat}_{product}_{roi}",
                bash_command=(
                    "curl --fail "
                    " --form measurement={{params.sat}}_{{params.product}} "
                    " --form tag_set=location={{params.roi}},"
                    "sensor={{params.sat}} "
                    " --form fields=mean,climatology,anomaly "
                    " --form time_column=Time "
                    " --form file=@./{{params.fpath}} "
                    " {{params.uploader_route}} "
                ),
                params={
                    "fpath": fpath,
                    "sat": sat.lower(),
                    "product": product,
                    "roi": roi,
                    "uploader_route": UPLOADER_ROUTE
                }
            )
            download_task >> upload_task
    # ========================================================================
    # Bouy Ingest
    # ========================================================================
    for roi in BOUY_ROI_LIST:
        for product in ['sal', 'temp']:
            fpath = f"{REGION}-_-SAL_TS_NDBC-_-{roi}_NDBC_{product}_FKdb.csv"
            download_task = BashOperator(
                task_id=f"download_bouy_{roi}_{product}",
                bash_command=(
                    "curl --fail "
                    "{{params.DATA_HOST}}/{{params.fpath}} "
                ),
                params={
                    "fpath": fpath,
                    "DATA_HOST": DATA_HOST
                }
            )
            upload_task = BashOperator(
                task_id=f"upload_bouy_{roi}_{product}",
                bash_command=(
                    "curl --fail "
                    ' --form measurement=bouy_{{params.product}} '
                    ' --form tag_set=location={{params.roi}},source=ndbc '
                    ' --form fields="mean,climatology,anomaly" '
                    ' --form time_column=time '
                    ' --form file=@./{{params.fpath}} '
                    ' {{params.uploader_route}} '
                ),
                params={
                    "fpath": fpath,
                    "product": product,
                    "roi": roi,
                    "uploader_route": UPLOADER_ROUTE
                }
            )
            download_task >> upload_task


    # ========================================================================
    # USGS River Discharge Ingest
    # ========================================================================
    for river in USGS_RIVER_LIST:
        fpath = f"{REGION}-_-DISCH_CSV_USGS-_-USGS_disch_{river}.csv}"
        download_task = BashOperator(
            task_id=f"download_river_{river}",
            bash_command=(
                "curl --fail "
                "{{params.DATA_HOST}}/{{params.fpath}} "
            ),
            params={
                "fpath": fpath,
                "DATA_HOST": DATA_HOST
            }
        )
        upload_task = BashOperator(
            task_id=f"upload_river_{river}",
            bash_command=(
                "curl --fail "
                ' --form measurement=river_discharge '
                ' --form tag_set=location={{params.river}},source=usgs '
                ' --form fields=mean,climatology,anomaly '
                ' --form time_column=time '
                ' --form file=@./{{params.fpath}} '
                ' {{params.uploader_route}} '
            ),
            params={
                "river": river,
                "uploader_route": UPLOADER_ROUTE
            }
        )
        download_task >> upload_task
