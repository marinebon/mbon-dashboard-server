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
    # === get the data from SOAP API

    # TODO: do this for each in:
    # {
    #     "wq": ['Temp','Sal','DO_mgl','pH','Turb','ChlFluor'],
    #     "met": ['ATemp','RH','BP','WSpd','Wdir','TotPAR','TotPrcp'],
    #     "nut": ['PO4F','NH4F','NO2F','NO3F','NO23F','CHLA_N'],
    # }
        
    # TODO: also the get the quality flags for each (eg `Sal_F`)
    # TODO: do this for each station code
    station_code_prefixes =  [
        'acebpmet',
        'acespnut',
        'acespwq'
        
        'sapmlmet'
        'gtmpcmet'
    ]
            
'gtm pcmet',
    ]
    def getData():
        """
        fetch met data based on docs from https://cdmo.baruch.sc.edu/webservices.cfm
        """
        station_code = "acespwq"  # ace sp wq
        param_name = "Sal"
        
        from suds.client import Client
        
        soapClient = Client("http://cdmo.baruch.sc.edu/webservices2/requests.cfc?wsdl", timeout=90, retxml=True)
        
        #Get the station codes SOAP request example.
        param_data = soapClient.service.exportSingleParamXML(
            station_code,  # Station_Code
            25,  # Number of records to retrieve TODO: make this inf?
            param_name",  # parameter
        )
        print(param_data)
        pd.write_csv(param_data, "./datafile.csv")
        
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
            'fields': 'Sal',
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

    
    download_data_task = PythonOperator(
        task_id='download_data_task',
        python_callable=getData
    )

