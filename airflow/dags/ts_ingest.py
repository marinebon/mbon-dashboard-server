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

REGION = 'SEUS'
DATA_HOST = "https://storage.googleapis.com/dashboards_csvs"

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
        '01', '02', '03', '04', '05', '06', '07', '08', '09',
        '10', '11', '12', '13', '14', '15', '16', '17','grnms'
    ]
    SAT_FILE_DETAIL_LIST = [
        # sat    | product
        ["MODA", "chlor_a"],
        ["MODA", "Rrs_667"],
        ["MODA", "Kd_490"],
        ["MODA", "sst4"],
        ["MODA",  "ABI"],
    ]
    # example path: `GOMdbv2_ABI_TS_MODA_daily_Alderice.csv`
    SAT_FPATH = (
        "{REGION}dbv23_{product}_TS_{sat}_daily_{roi}.csv"
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
       'GR_MET_BUOY'
    ]
    # example filname: GR_MET_BUOY_NDBC_stdmet_atemp_SEUSdb.csv
    BOUY_FPATH = "{roi}_NDBC_stdmet_{product}_SEUSdb.csv"
    for roi in BOUY_ROI_LIST:
       for product in ['wdir','wspd','gust','atemp','wtemp','barp','wvht','dwpd','awpd','mwd']:
           BashOperator(
               task_id=f"ingest_bouy_{roi}_{product}",
               bash_command=(
                   "curl --fail-with-body "
                   "    {{params.DATA_HOST}}/{{params.fpath}} "
                   "    > datafile.csv"
                   " && curl --fail-with-body "
                   '    --form measurement=bouy_{{params.product}} '
                   '    --form tag_set=location={{params.roi}},source=ndbc '
                   '    --form fields=data '
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
    # USGS Gage Height Ingest
    # ========================================================================
    USGS_RIVER_LIST = ['SavannahRv','HudsonCr','AltamahaRv','SatillaRv','StJohnsRv','OgeecheeRv','BrunswickRv','StMarysRv']
    # example fname: USGS_gh_SavannahRv_SEUSdb.csv
    RIVER_FPATH = "USGS_gh_{river}_SEUSdb.csv"
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
    # ========================================================================
    # USGS Water Quality Ingest
    # ========================================================================
    # TODO
    # ========================================================================
    # NERRS Water Quality Ingest (temporary - will be replaced)
    # ========================================================================
NERR_ROI_LIST = [
        'HuntDock', 'LowerDuplin', 'CabCr', 'DeanCr'
    ]
    NERR_FILE_DETAIL_LIST = [
        # suite    | product
        ["WQ", "Temp"],
        ["WQ", "DO_mgl"],
        ["WQ", "Turb"],
        ["WQ", "pH"],
        ["WQ",  "Sal"],
    ]
    # example path: `SAP_CabCr_Sal_NERR_WQ_HIST_SEUSdb.csv`
    SAT_FPATH = (
        "SAP_{roi}_{product}_NERR_{suite}_HIST_{region}db.csv"
    )
    for roi in NERR_ROI_LIST:
        for suite, product in NERR_FILE_DETAIL_LIST:
            BashOperator(
                task_id=f"ingest_nerrwq_roi_{REGION}_{suite}_{product}_{roi}",
                bash_command=(
                    "curl --location --fail-with-body "
                    "    {{params.DATA_HOST}}/{{params.fpath}} "
                    "    > datafile.csv "
                    " && head datafile.csv "
                    " && curl --location --fail-with-body "
                    "    --form measurement={{params.suite}}_{{params.product}} "
                    "    --form tag_set=location={{params.roi}},"
                        "sensor={{params.suite}} "
                    "    --form fields=mean,climatology,anomaly "
                    "    --form time_column=Time "
                    "    --form file=@./datafile.csv "
                    "    {{params.uploader_route}} "
                ),
                params={
                    "suite": suite.lower(),
                    "product": product,
                    "roi": roi,
                    "uploader_route": UPLOADER_ROUTE,
                    "fpath": SAT_FPATH.format(**vars()),
                    "DATA_HOST": DATA_HOST
                }
            )




