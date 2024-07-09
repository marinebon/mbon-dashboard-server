"""
Ingest NERRS met data.
Instrumented records (continuous, but only from one location at each NERR)

```mermaid
"NERRS CDMO" 
  -- "airflow ingest_nerr_met" --> influxDB 
"""
import os

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

from nerrs2influx import nerrs2influx

# These jobs run once to grab all the data.
# TODO: modify to only grab latest data.
with DAG(
    'ingest_nerrs_met',
    catchup=True,
    schedule_interval="0 0 * * *",
    max_active_runs=1,
    default_args={
        "start_date": datetime(2020, 1, 1),
        #'retries': 3,
        #'retry_delay': timedelta(days=1),
    },
) as dag:
    # TODO: do this for each in:
    NERR_PRODUCTS = {
#        "wq": ['Temp','Sal','DO_mgl','pH','Turb','ChlFluor'],
        "met": ['ATemp','RH','BP','WSpd','Wdir','TotPAR','TotPrcp'],
#        "nut": ['PO4F','NH4F','NO2F','NO3F','NO23F','CHLA_N'],
    }
        
    # TODO: also the get the quality flags for each (eg `Sal_F`)?
    NERR_ROI_LIST = {  # all of these are Sapelo (sap)
        "sap": [
            ["hd", 'HuntDock'], 
            ["ld", 'LowerDuplin'], 
            ["ca", 'CabCr'], 
            ["dc", 'DeanCr']
        ]
    }

    #NAME_ABBREV_MAP = {
    #    'HuntDock': 'saphd',
    #    'LowerDuplin': 'sapld',
    #    'CabCr': 'sapca'
    #    'DeanCr': 'sapdc'
    #}
    # 
    #STATION_PARAMS = {
    #    'HuntDock': [
    #        'wq_Temp', 'wq_Sal', 'wq_DO', 'wq_pH', 'wq_Turb',
    #        'nut_PO4F', 'nut_NH4F', 'nut_NO2F', 'nut_NO23F'
    #    ],
    #    'LowerDuplin': [
    #        'wq_Temp', 'wq_Sal', 'wq_DO', 'wq_pH', 'wq_Turb'
    #    ],
    #    'CabCr': [
    #        'wq_Temp', 'wq_Sal', 'wq_DO', 'wq_pH', 'wq_Turb',
    #        'nut_PO4F', 'nut_NH4F', 'nut_NO2F', 'nut_NO23F'
    #    ],
    #    'DeanCr': [
    #        'wq_Temp', 'wq_Sal', 'wq_DO', 'wq_pH', 'wq_Turb',
    #        'nut_PO4F', 'nut_NH4F', 'nut_NO2F', 'nut_NO23F'
    #    ]
    #}
    
    # example path: `SAP_CabCr_Sal_NERR_WQ_HIST_SEUSdb.csv`
    NERR_FPATH = "SAP_{station_name}_{product}_NERR_{suite}_HIST_SEUSdb.csv"
    for nerr_abbrev, stations in NERR_ROI_LIST.items():
        for station in stations:
            station_abbrev = station[0]
            station_name = station[1]
            for suite, product_list in NERR_PRODUCTS.items():
                for product in product_list:
                    station_code = f"{nerr_abbrev}{station_abbrev}{suite}"
                    PythonOperator(
                        task_id=f"ingest_nerrs_{suite}_{product}_{station_name}",
                        python_callable=nerrs2influx,
                        op_kwargs={
                            'station_name': station_name,
                            'station_code': station_code,  # "acespwq"  # ace sp wq
                            'suite': suite,
                            'product': product # "Sal"
                        },
                    )

