"""
Ingests all timeseries .csv files into influxdb using mbon_data_uploader.
"""
import os

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime

DAGS_DIR = "/usr/local/airflow/dags/"


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
    region = 'fk'
    fname_prefix = 'FKdbv2'
    for roi in [
        'BB', 'BIS', 'CAR', 'DT', 'DTN', 'EFB', 'EK_IN', 'EK_MID', 'FKNMS',
        'FLB', 'FROCK', 'IFB', 'KW', 'LK', 'MIA', 'MK', 'MOL', 'MQ', 'MR',
        'MUK', 'PBI', 'PEV', 'SANDK', 'SFP10', 'SFP11', 'SFP12', 'SFP13',
        'SFP14', 'SFP15_5', 'SFP15', 'SFP16', 'SFP17', 'SFP18', 'SFP19',
        'SFP1', 'SFP20', 'SFP21_5', 'SFP22_5', 'SFP22', 'SFP23', 'SFP24',
        'SFP2', 'SFP30_5', 'SFP31', 'SFP32', 'SFP33', 'SFP34', 'SFP39',
        'SFP40', 'SFP41', 'SFP42', 'SFP45', 'SFP46', 'SFP47', 'SFP48', 'SFP49',
        'SFP4', 'SFP50', 'SFP51', 'SFP52', 'SFP53', 'SFP54', 'SFP5_5',
        'SFP55', 'SFP56', 'SFP57_2', 'SFP57_3', 'SFP57', 'SFP5', 'SFP61',
        'SFP62', 'SFP63', 'SFP64', 'SFP6_5', 'SFP61', 'SFP62', 'SFP63',
        'SFP64', 'SFP6_5', 'SFP65', 'SFP66', 'SFP67', 'SFP69', 'SFP6', 'SFP70',
        'SFP7', 'SFP8', 'SFP9_5', 'SFP9', 'SUG', 'SLI', 'SOM', 'SR', 'UFB1',
        'UFB2', 'UFB4', 'UK', 'UK_IN', 'UK_MID', 'UK_OFF', 'WFB', 'WFS', 'WS'
    ]:
        for sat, product_type, product in [
            ["VSNPP", "OC", "chlor_a"],
            ["VSNPP", "OC", "Rrs_671"],
            ["VSNPP", "OC", "Kd_490"],
            ["VSNPP", "SSTN", "sstn"],
            ["MODA", "OC", "ABI"],
        ]:
            BashOperator(
                task_id=f"sat_roi_{region}_{sat}_{product}_{roi}",
                bash_command=(
                    " curl "
                    " --form measurement=${measurement} "
                    " --form tag_set=location=${roi},sensor=${sat} "
                    " --form fields=mean,climatology,anomaly "
                    " --form time_column=time "
                    " --form file=@/srv/imars-objects/${region}/"
                    "EXT_TS_{{SAT}}/${product_type}/"
                    "${fname_prefix}_${product}_TS_${SAT}_"
                    "daily_${roi}.csv "
                    " ${uploader_route}"
                ),
                env={
                    "SAT": sat,
                    "sat": sat.lower(),
                    "region": "fk",
                    "product_type": product_type,
                    "fname_prefix": fname_prefix,
                    "product": product,
                    "roi": roi,
                    "uploader_route": UPLOADER_ROUTE
                }
            )
    # ========================================================================
    # Bouy Ingest
    # ========================================================================
    for roi in [
        'BUTTERNUT', 'WHIPRAY', 'PETERSON', 'BOBALLEN', 'LITTLERABBIT'
    ]:
        for product in ['sal', 'temp']:
            BashOperator(
                task_id=f"bouy_{roi}_{product}",
                bash_command=(
                    'curl '
                    ' --form measurement=bouy_${product} '
                    ' --form tag_set=location=${roi},source=ndbc '
                    ' --form fields="mean,climatology,anomaly" '
                    ' --form time_column=time '
                    ' --form file=@/srv/imars-objects/${region}/SAL_TS_NDBC/'
                    '${roi}_NDBC_${product}_FKdb.csv '
                    ' ${uploader_route}'
                ),
                env={
                    "product": product,
                    "region": region,
                    "roi": roi,
                    "uploader_route": UPLOADER_ROUTE
                }
            )

    # ========================================================================
    # USGS River Discharge Ingest
    # ========================================================================
    for river in ['FKdb', "FWCdb_EFL"]:
        BashOperator(
            task_id=f"river_{river}",
            bash_command=(
                ' curl '
                ' --form measurement=river_discharge '
                ' --form tag_set=location=${river},source=usgs '
                ' --form fields=mean,climatology,anomaly '
                ' --form time_column=time '
                ' --form file=@/srv/imars-objects/${region}/DISCH_CSV_USGS/'
                'USGS_disch_${river}.csv '
                ' ${uploader_route}'
            ),
            env={
                "river": river,
                "region": region,
                "uploader_route": UPLOADER_ROUTE
            }
        )
