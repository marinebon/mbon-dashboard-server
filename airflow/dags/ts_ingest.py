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
                    "curl --fail-with-body "
                    "    {{params.DATA_HOST}}/{{params.fpath}} "
                    "    > datafile.csv"
                    " && curl --fail-with-body "
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
    USGS_RIVER_LIST = ['FKdb', "FWCdb_EFL", "FWCdb_STL"]
    # example fname: USGS_disch_FWCdb_STL.csv
    RIVER_FPATH = "USGS_disch_{river}.csv"
    for river in USGS_RIVER_LIST:
        BashOperator(
            task_id=f"ingest_river_{river}",
            bash_command=(
                "curl --fail-with-body "
                "    {{params.DATA_HOST}}/{{params.fpath}} "
                "    > datafile.csv"
                " && curl --fail-with-body "
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
