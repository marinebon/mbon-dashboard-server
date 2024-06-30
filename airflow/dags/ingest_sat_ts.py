"""
Ingests all timeseries .csv.

```mermaid
imars_netcdfs 
  -- "dotis matlab cron" --> "anom+clim csv files"
  -- "dotis cron" --> gbucket
  -- "airflow ingest_sat_ts" --> influxDB
```
"""
import os

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

from csv2influx import csv2influx

REGION = 'SEUS'
DATA_HOST = "https://storage.googleapis.com/dashboards_csvs"

REGION_UPPERCASE = REGION.upper()  # bc cannot do REGION.upper() inside f string.
# ============================================================================
# === DAG defines the task exec order
# ============================================================================
with DAG(
    'ingest_sat_ts',
    catchup=False,  # latest only
    schedule_interval="0 0 * * *",
    max_active_runs=1,
    default_args={
        "start_date": datetime(2020, 1, 1)
    },
) as dag:
    GBUCKET_URL_PREFIX = "https://storage.googleapis.com/dashboards_csvs"
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
    for roi in SAT_ROI_LIST:
        for sat, product in SAT_FILE_DETAIL_LIST:
            # example path: `GOMdbv2_ABI_TS_MODA_daily_Alderice.csv`
            DATA_FNAME = f"{REGION}dbv23_{product}_TS_{sat}_daily_{roi}.csv"
            PythonOperator(
                task_id=f"ingest_sat_{roi}_{sat}_{product}",
                python_callable=csv2influx,
                op_kwargs={
                    'data_url': f"{GBUCKET_URL_PREFIX}/{DATA_FNAME}",
                    'measurement': product,
                    'fields': [
                        ["mean", "mean"],
                        ["climatology", "climatology"],
                        ["anomaly", "anomaly"]
                    ],
                    'tags': [
                        ['satellite', sat],
                        ['location', roi]
                    ],
                    'timeCol': "Time"
                },
            )

            
    # ========================================================================
    # Bouy Ingest
    # ========================================================================
    BOUY_ROI_LIST = [
       'GR_MET_BUOY'
    ]
    # example filname: GR_MET_BUOY_NDBC_stdmet_atemp_SEUSdb.csv
    BOUY_FPATH = "{roi}_NDBC_stdmet_{product}_SEUSdb.csv"
#    for roi in BOUY_ROI_LIST:
#       for product in ['wdir','wspd','gust','atemp','wtemp','barp','wvht','dwpd','awpd','mwd']:
#           BashOperator(
#               task_id=f"ingest_bouy_{roi}_{product}",
#               bash_command=(
#                   "curl --fail-with-body "
#                   "    {{params.DATA_HOST}}/{{params.fpath}} "
#                   "    > datafile.csv"
#                   " && curl --fail-with-body "
#                   '    --form measurement=bouy_{{params.product}} '
#                   '    --form tag_set=location={{params.roi}},source=ndbc '
#                   '    --form fields=data '
#                   '    --form time_column=time '
#                   '    --form file=@./datafile.csv '
#                   '    {{params.uploader_route}} '
#               ),
#               params={
#                   "product": product,
#                   "roi": roi,
#                   "uploader_route": UPLOADER_ROUTE,
#                   "fpath": BOUY_FPATH.format(**vars()),
#                   "DATA_HOST": DATA_HOST
#               }
#           )
    # ========================================================================
    # NERRS Water Quality Ingest (Not working, temporary - will be replaced)
    # ========================================================================
    NERR_ROI_LIST = [
           'HuntDock', 'LowerDuplin', 'CabCr', 'DeanCr'
    ]
    NERR_FILE_DETAIL_LIST = [
        # suite | product
        ["WQ", "Temp"],
        ["WQ", "DO_mgl"],
        ["WQ", "Turb"],
        ["WQ", "pH"],
        ["WQ", "Sal"],
        ["NUT", "CHLA_N"],
        ["NUT", "NH4F"],
        ["NUT", "NO2F"],
        ["NUT", "PO4F"],
        ["NUT", "NO23F"],
        ["NUT", "NO3F"],
    ]
    # example path: `SAP_CabCr_Sal_NERR_WQ_HIST_SEUSdb.csv`
    NERR_FPATH = "SAP_{roi}_{product}_NERR_{suite}_HIST_SEUSdb.csv"
  #  for roi in NERR_ROI_LIST:
  #     for suite, product in NERR_FILE_DETAIL_LIST:
  #         BashOperator(
  #             task_id=f"ingest_nerrwq_roi_{REGION}_{suite}_{product}_{roi}",
  #             bash_command=(
  #                 "curl --location --fail-with-body "
  #                 "    {{params.DATA_HOST}}/{{params.fpath}} "
  #                 "    > datafile.csv "
  #                 " && head datafile.csv "
  #                 " && curl --location --fail-with-body "
  #                 "    --form measurement={{params.suite}}_{{params.product}} "
  #                 "    --form tag_set=location={{params.roi}},"
  #                     "sensor={{params.suite}} "
  #                 "    --form fields=mean,climatology,anomaly "
  #                 "    --form time_column=time "
  #                 "    --form file=@./datafile.csv "
  #                 "    {{params.uploader_route}} "
  #             ),
  #             params={
  #                 "suite": suite.lower(),
  #                 "product": product,
  #                 "roi": roi,
  #                 "uploader_route": UPLOADER_ROUTE,
  #                 "fpath": NERR_FPATH.format(**vars()),
  #                 "DATA_HOST": DATA_HOST
  #             }
  #         )
