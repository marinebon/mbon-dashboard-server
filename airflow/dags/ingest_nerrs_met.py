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

suite = 'met'
# station list from                                                                               
#    python3 -c 'from nerrs_data.exportStationCodes import exportStationCodesDictFor; exportStationCodesDictFor("sap")'                                                                                
stations = [
    {"NERR_SITE_ID":"sap","Station_Code":"sapmlmet","Station_Name":"Marsh Landing","status":"Active"\
,"active_dates":"Sep 2002-","state":"ga","reserve_name":"Sapelo Island","params_reported":["ATemp","R\
H","BP","WSpd","MaxWSpd","MaxWSpdT","Wdir","SDWDir","TotPrcp","TotPAR","CumPrcp","TotSoRad"],"Real_ti\
me":"R"} ,
]


# TODO: set start_date using station['active_dates']
# TODO: specify frequency of data?
# TODO: modify nerrs2influx to use dates
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
    # example path: `SAP_CabCr_Sal_NERR_WQ_HIST_SEUSdb.csv`
    NERR_FPATH = "SAP_{station_name}_{product}_NERR_{suite}_HIST_SEUSdb.csv"
    for station in stations:
        for param in station['parameters_reported']:
            PythonOperator(
                task_id=f"ingest_nerrs_{suite}_{product}_{station_name}",
                python_callable=nerrs2influx,
                op_kwargs={
                    'station_name': station['Station_Name'],
                    'station_code': station['NERR_SITE_ID'],  # "acespwq"  # ace sp wq                   
                    'suite': ,
                    'product': product # "Sal"                                                
                },
            )
            


