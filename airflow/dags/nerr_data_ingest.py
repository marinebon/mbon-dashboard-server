"""
Ingest bouy data 
"""
import os

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

# These jobs run once to grab all the data.
# TODO: modify to only grab latest data.
with DAG(
    'nerr_data_ingest',
    catchup=False,
    schedule_interval="0 0 * * *",
    max_active_runs=1,
    default_args={
        "start_date": datetime(2023, 6, 20),
        #'retries': 3,
        #'retry_delay': timedelta(days=1),
    },
) as dag:
    def nerrs2influx(station_code, param_name):
        """
        fetch met data based on docs from https://cdmo.baruch.sc.edu/webservices.cfm
        """
        import nerrs_data
        import pandas as pd
        param_data = nerrs_data.getData(station_code, param_name)
        param_data.to_csv("./datafile.csv")
        
        # === upload the data
        import requests

        UPLOADER_HOSTNAME = os.environ["UPLOADER_HOSTNAME"]
        if UPLOADER_HOSTNAME.endswith('/'):  # rm possible trailing /
            UPLOADER_HOSTNAME = UPLOADER_HOSTNAME[:-1]
        UPLOADER_ROUTE = UPLOADER_HOSTNAME + "/submit/sat_image_extraction"

        url = UPLOADER_ROUTE  # Replace this with your actual URL
        data = {
            'measurement': 'nerrs_met_data',
            'tag_set': 'station_code=SPOT30987C',
            'fields': param_name,
            'time_column': 'utc_timestamp',
        }
        
        files = {
            'file': ('datafile.csv', open('./datafile.csv', 'rb'))
        }
        
        response = requests.post(url, data=data, files=files)
        
        if response.status_code == 200:
            print("Upload successful")
        else:
            print(f"Upload failed with status code {response.status_code}")
            print(response.text)
            raise ValueError(response.text)

    
    # TODO: do this for each in:
    NERR_PRODUCTS = {
        "wq": ['Temp','Sal','DO_mgl','pH','Turb','ChlFluor'],
        "met": ['ATemp','RH','BP','WSpd','Wdir','TotPAR','TotPrcp'],
        "nut": ['PO4F','NH4F','NO2F','NO3F','NO23F','CHLA_N'],
    }
        
    # TODO: also the get the quality flags for each (eg `Sal_F`)?
    NERR_ROI_LIST = [
           'HuntDock', 'LowerDuplin', 'CabCr', 'DeanCr'
    ]

    # example path: `SAP_CabCr_Sal_NERR_WQ_HIST_SEUSdb.csv`
    NERR_FPATH = "SAP_{roi}_{product}_NERR_{suite}_HIST_SEUSdb.csv"
    for roi in NERR_ROI_LIST:
       for suite, product_list in NERR_PRODUCTS.items():
           for product in product_list:
                PythonOperator(
                    task_id=f"ingest_nerr_{suite}_{product}_{roi}",
                    python_callable=nerrs2influx,
                    op_kwargs={
                        'station_code': roi,  # "acespwq"  # ace sp wq
                        'param_name': product # "Sal"
                    },
                )

