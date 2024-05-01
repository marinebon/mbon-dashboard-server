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
    def nerrs2influx(station_name, station_code, suite, product):
        """
        fetch met data based on docs from https://cdmo.baruch.sc.edu/webservices.cfm
        """
        import nerrs_data
        import pandas as pd
        param_data = nerrs_data.getData(station_code, product)
        param_data.to_csv("./datafile.csv")
        
        # === upload the data
        import requests

        UPLOADER_HOSTNAME = os.environ["UPLOADER_HOSTNAME"]
        if UPLOADER_HOSTNAME.endswith('/'):  # rm possible trailing /
            UPLOADER_HOSTNAME = UPLOADER_HOSTNAME[:-1]
        UPLOADER_ROUTE = UPLOADER_HOSTNAME + "/submit/sat_image_extraction"

        url = UPLOADER_ROUTE  # Replace this with your actual URL
        data = {
            'measurement': f"{suite}_{product}",
            'tag_set': f'station_code={station_code},location={station_name},sensor={suite}',
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
    NERR_ROI_LIST = {  # all of these are Sapelo (sap)
        "sap": [
            ["hd", 'HuntDock'], 
            ["ld", 'LowerDuplin'], 
            ["ca", 'CabCr'], 
            ["dc", 'DeanCr']
        ]
    }

    # example path: `SAP_CabCr_Sal_NERR_WQ_HIST_SEUSdb.csv`
    NERR_FPATH = "SAP_{station_name}_{product}_NERR_{suite}_HIST_SEUSdb.csv"
    for nerr_abbrev, stations in NERR_ROI_LIST.items():
        for station in stations:
            station_abbrev = station[0]
            station_name = station[1]
            for suite, product_list in NERR_PRODUCTS.items():
                for product in product_list:
                    PythonOperator(
                        task_id=f"ingest_nerr_{suite}_{product}_{station_name}",
                        python_callable=nerrs2influx,
                        op_kwargs={
                            'station_name': station_name,
                            'station_code': f"{nerr_abbrev}{station_abbrev}{suite}",  # "acespwq"  # ace sp wq
                            'suite': suite,
                            'param_name': product # "Sal"
                        },
                    )

