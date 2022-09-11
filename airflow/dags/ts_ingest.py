"""
Ingests all timeseries .csv files into influxdb using mbon_data_uploader.
The timeseries are ingested from a public github repo folder.

!!! NOTE how the dir separator (/) is replaced w/ -_- in the FPATH variables
below.
"""
import os

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime

REGION = 'GOM'
DATA_HOST = "https://raw.githubusercontent.com/7yl4r/extracted_sat_ts_gom_csv_data/main/data"

REGION_UPPERCASE = REGION.upper()  # bc cannot do REGION.upper() inside f string.
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
    SAT_ROI_LIST = [
        'WFG', 'EFG', 'STET', 'COAST1', 'COAST2', 'COAST3', 'COAST4', 'SS1',
        'SS2', 'SS3', 'SS4', 'SS5', 'SS6', 'SS7', 'SS8'
    ]
    SAT_FILE_DETAIL_LIST = [
        # sat    | product
        ["VSNPP", "chlor_a"],
        ["VSNPP", "Rrs_671"],
        ["VSNPP", "Kd_490"],
        ["VSNPP", "sstn"],
        ["MODA",  "ABI"],
    ]
    # example path: `GOMdbv2_ABI_TS_MODA_daily_Alderice.csv`
    SAT_FPATH = (
        "{REGION}dbv2_{product}_TS_{sat}_daily_{roi}.csv"
    )
    for roi in SAT_ROI_LIST:
        for sat, product in SAT_FILE_DETAIL_LIST:
            BashOperator(
                task_id=f"ingest_sat_roi_{REGION}_{sat}_{product}_{roi}",
                bash_command=(
                    "curl --location --fail-with-body "
                    "    {{params.DATA_HOST}}/{{params.fpath}} "
                    "    > datafile.csv "
                    " && head datafile.csv "
                    " && curl --location --fail-with-body "
                    "    --form measurement={{params.sat}}_{{params.product}} "
                    "    --form tag_set=location={{params.roi}},"
                        "sensor={{params.sat}} "
                    "    --form fields=mean,climatology,anomaly "
                    "    --form time_column=Time "
                    "    --form file=@./datafile.csv "
                    "    {{params.uploader_route}} "
                ),
                params={
                    "sat": sat.lower(),
                    "product": product,
                    "roi": roi,
                    "uploader_route": UPLOADER_ROUTE,
                    "fpath": SAT_FPATH.format(**vars()),
                    "DATA_HOST": DATA_HOST
                }
            )
    # ========================================================================
    # Bouy Ingest
    # ========================================================================
    BOUY_ROI_LIST = [
        'BUTTERNUT', 'WHIPRAY', 'PETERSON', 'BOBALLEN', 'LITTLERABBIT'
    ]
    # example filname: BUTTERNUT_NDBC_sal_FKdb.csv
    BOUY_FPATH = "{roi}_NDBC_{product}_FKdb.csv"
    for roi in BOUY_ROI_LIST:
        for product in ['sal', 'temp']:
            BashOperator(
                task_id=f"ingest_bouy_{roi}_{product}",
                bash_command=(
                    "curl --location --fail-with-body "
                    "    {{params.DATA_HOST}}/{{params.fpath}} "
                    "    > datafile.csv"
                    " && head datafile.csv "
                    " && curl --location --fail-with-body "
                    '    --form measurement=bouy_{{params.product}} '
                    '    --form tag_set=location={{params.roi}},source=ndbc '
                    '    --form fields="mean,climatology,anomaly" '
                    '    --form time_column=time '
                    '    --form file=@./datafile.csv '
                    '    {{params.uploader_route}} '
                ),
                params={
                    "product": product,
                    "roi": roi,
                    "uploader_route": UPLOADER_ROUTE,
                    "fpath": BOUY_FPATH.format(**vars()),
                    "DATA_HOST": DATA_HOST
                }
            )

    # ========================================================================
    # USGS River Discharge Ingest
    # ========================================================================
    # example fname: USGS_disch_FWCdb_STL.csv
    RIVER_FPATH = "USGS_disch_{river}.csv"
    USGS_RIVER_LIST = ['FGBdb_MS', 'FGBdb_TX']
    for river in USGS_RIVER_LIST:
        BashOperator(
            task_id=f"ingest_river_{river}",
            bash_command=(
                "curl --location --fail-with-body "
                "    {{params.DATA_HOST}}/{{params.fpath}} "
                "    > datafile.csv"
                " && head datafile.csv "
                " && curl --location --fail-with-body "
                '    --form measurement=river_discharge '
                '    --form tag_set=location={{params.river}},source=usgs '
                '    --form fields=mean,climatology,anomaly '
                '    --form time_column=time '
                '    --form file=@./datafile.csv '
                '    {{params.uploader_route}} '
            ),
            params={
                "river": river,
                "uploader_route": UPLOADER_ROUTE,
                "fpath": RIVER_FPATH.format(**vars()),
                "DATA_HOST": DATA_HOST
            }
        )
