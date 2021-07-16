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

SAT_ROI_LIST = [
    'BB', 'BIS', 'CAR', 'DT', 'DTN', 'EFB', 'EK_IN', 'EK_MID', 'FKNMS',
    'FLB', 'FROCK', 'IFB', 'KW', 'LK', 'MIA', 'MK', 'MOL', 'MQ', 'MR',
    'MUK', 'PBI', 'PEV', 'SANDK', 'SFP10', 'SFP11', 'SFP12', 'SFP13',
    'SFP14', 'SFP15_5', 'SFP15', 'SFP16', 'SFP17', 'SFP18', 'SFP19',
    'SFP1', 'SFP20', 'SFP21_5', 'SFP22_5', 'SFP22', 'SFP23', 'SFP24',
    'SFP2', 'SFP30_5', 'SFP31', 'SFP32', 'SFP33', 'SFP34', 'SFP39',
    'SFP40', 'SFP41', 'SFP42', 'SFP45', 'SFP46', 'SFP47', 'SFP48', 'SFP49',
    'SFP4', 'SFP50', 'SFP51', 'SFP52', 'SFP53', 'SFP54', 'SFP5_5',
    'SFP55', 'SFP56', 'SFP57_2', 'SFP57_3', 'SFP57', 'SFP5',
    'SFP6_5', 'SFP61', 'SFP62', 'SFP63',
    'SFP64', 'SFP65', 'SFP66', 'SFP67', 'SFP69', 'SFP6', 'SFP70',
    'SFP7', 'SFP8', 'SFP9_5', 'SFP9', 'SUG', 'SLI', 'SOM', 'SR', 'UFB1',
    'UFB2', 'UFB4', 'UK', 'UK_IN', 'UK_MID', 'UK_OFF', 'WFB', 'WFS', 'WS'
]
SAT_FILE_DETAIL_LIST = [
    ["VSNPP", "OC", "chlor_a"],
    ["VSNPP", "OC", "Rrs_671"],
    ["VSNPP", "OC", "Kd_490"],
    ["VSNPP", "SSTN", "sstn"],
    ["MODA", "OC", "ABI"],
]
SAT_FPATH = "{REGION}-_-EXT_TS_{sat}-_-{product_type}-_-{REGION.upper()}dbv2_{product}_TS_{sat}_daily_{roi}.csv"

BOUY_ROI_LIST = [
    'BUTTERNUT', 'WHIPRAY', 'PETERSON', 'BOBALLEN', 'LITTLERABBIT'
]
BOUY_FPATH = "{REGION}-_-SAL_TS_NDBC-_-{roi}_NDBC_{product}_FKdb.csv"

USGS_RIVER_LIST = ['FKdb', "FWCdb_EFL", "FWCdb_STL"]
RIVER_FPATH = "{REGION}-_-DISCH_CSV_USGS-_-USGS_disch_{river}.csv"

# ============================================================================
# === this code prints out the symlinks needed
# ============================================================================
# NOTE: if you want to remove all the broken symlinks use:
#       find ~/public_html/ -xtype l -delete
def print_link_bash(fpath):
    """prints out the bash to create required symlink"""
    print(f"ln -s /srv/imars-objects/{fpath.replace('-_-', '/')} /srv/imars-objects/homes/tylar/public_html/{fpath}")

# These loops are expected to be identical to the lines further down in this
# file which define the tasks.
for roi in SAT_ROI_LIST:
    for sat, product_type, product in SAT_FILE_DETAIL_LIST:
        print_link_bash(SAT_FPATH.format(**vars()))
for roi in BOUY_ROI_LIST:
    for product in ['sal', 'temp']:
        print_link_bash(BOUY_FPATH.format(**vars()))
for river in USGS_RIVER_LIST:
    print_link_bash(RIVER_FPATH.format(**vars()))
# ============================================================================

# ============================================================================
# === DAG defines the task exec order
# ============================================================================
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
            fpath = SAT_FPATH.format(**vars())
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
            fpath = BOUY_FPATH.format(**vars())
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
        fpath = RIVER_FPATH.format(**vars())
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
