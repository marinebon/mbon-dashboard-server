"""
Ingest NERRS met data.
Instrumented records (continuous, but only from one location at each NERR)

```mermaid
"NERRS CDMO" 
  -- "airflow ingest_nerrs" --> influxDB 
"""
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

from nerrs2influx import nerrs2influx

# station list from                                                                               
#    python3 -c 'from nerrs_data.exportStationCodes import exportStationCodesDictFor; exportStationCodesDictFor("sap")'                                                                                
STATIONS = [
    # met
    {"NERR_SITE_ID":"sap","Station_Code":"sapmlmet","Station_Name":"Marsh Landing","status":"Active"\
,"active_dates":"Sep 2002-","state":"ga","reserve_name":"Sapelo Island","params_reported":["ATemp","R\
H","BP","WSpd","MaxWSpd","Wdir","SDWDir","TotPrcp","TotPAR","CumPrcp","TotSoRad"],"Real_ti\
me":"R"} ,

    # nut
    {"NERR_SITE_ID":"sap","Station_Code":"sapcanut","Station_Name":"Cabretta Creek","status":"Active","active_dates":"Aug 2004-","state":"ga","reserve_name":"Sapelo Island","params_reported":["NO23F","PO4F","CHLA_N","NO3F","NO2F","NH4F"],"Real_time":""} ,
    {"NERR_SITE_ID":"sap","Station_Code":"sapdcnut","Station_Name":"Dean Creek","status":"Active","active_dates":"May 2004-","state":"ga","reserve_name":"Sapelo Island","params_reported":["NO23F","PO4F","CHLA_N","NO3F","NO2F","NH4F"],"Real_time":""} ,
    {"NERR_SITE_ID":"sap","Station_Code":"sapfdnut","Station_Name":"Flume Dock","status":"Inactive","active_dates":"Mar 2002-Aug 2004","state":"ga","reserve_name":"Sapelo Island","params_reported":["NO23F","PO4F","CHLA_N","NO3F","NO2F","NH4F"],"Real_time":""} ,
    {"NERR_SITE_ID":"sap","Station_Code":"saphdnut","Station_Name":"Hunt Dock","status":"Active","active_dates":"Mar 2002-","state":"ga","reserve_name":"Sapelo Island","params_reported":["NO23F","PO4F","CHLA_N","NO3F","NO2F","NH4F"],"Real_time":""} ,
    {"NERR_SITE_ID":"sap","Station_Code":"sapldnut","Station_Name":"Lower Duplin","status":"Active","active_dates":"Jan 2002-","state":"ga","reserve_name":"Sapelo Island","params_reported":["NO23F","PO4F","CHLA_N","NO3F","NO2F","NH4F"],"Real_time":""} ,
    {"NERR_SITE_ID":"sap","Station_Code":"sapmlnut","Station_Name":"Marsh Landing","status":"Inactive","active_dates":"Jan 2002-2004","state":"ga","reserve_name":"Sapelo Island","params_reported":["NO23F","PO4F","CHLA_N","NO3F","NO2F","NH4F"],"Real_time":""} ,

    # wq
    {"NERR_SITE_ID":"sap","Station_Code":"sapbcwq","Station_Name":"Barn Creek","status":"Inactive","active_dates":"May 1995-Dec 1997","state":"ga","reserve_name":"Sapelo Island","params_reported":["Temp","SpCond","Sal","DO_pct","DO_mgl","pH","Turb"],"Real_time":""} ,
    {"NERR_SITE_ID":"sap","Station_Code":"sapcawq","Station_Name":"Cabretta Creek","status":"Active","active_dates":"Aug 2004-","state":"ga","reserve_name":"Sapelo Island","params_reported":["Temp","SpCond","Sal","DO_pct","DO_mgl","Depth","pH","Turb"],"Real_time":""} ,
    {"NERR_SITE_ID":"sap","Station_Code":"sapdcwq","Station_Name":"Dean Creek","status":"Active","active_dates":"May 2004-","state":"ga","reserve_name":"Sapelo Island","params_reported":["Temp","SpCond","Sal","DO_pct","DO_mgl","Depth","pH","Turb"],"Real_time":""} ,
    {"NERR_SITE_ID":"sap","Station_Code":"sapfdwq","Station_Name":"Flume Dock","status":"Inactive","active_dates":"Jan 1995-Dec 1998; Jun 2002-Aug 2004","state":"ga","reserve_name":"Sapelo Island","params_reported":["Temp","SpCond","Sal","DO_pct","DO_mgl","Depth","pH","Turb"],"Real_time":""} ,
    {"NERR_SITE_ID":"sap","Station_Code":"saphdwq","Station_Name":"Hunt Dock","status":"Active","active_dates":"Jul 1999-","state":"ga","reserve_name":"Sapelo Island","params_reported":["Temp","SpCond","Sal","DO_pct","DO_mgl","Depth","pH","Turb"],"Real_time":""} ,
    {"NERR_SITE_ID":"sap","Station_Code":"sapldwq","Station_Name":"Lower Duplin","status":"Active","active_dates":"Jan 1999-","state":"ga","reserve_name":"Sapelo Island","params_reported":["Temp","SpCond","Sal","DO_pct","DO_mgl","Depth","pH","Turb"],"Real_time":"R"} ,
    {"NERR_SITE_ID":"sap","Station_Code":"sapmlwq","Station_Name":"Marsh Landing","status":"Inactive","active_dates":"May 1995-Dec 1998; Jun 2002-May 2004","state":"ga","reserve_name":"Sapelo Island","params_reported":["Temp","SpCond","Sal","DO_pct","DO_mgl","Depth","pH","Turb"],"Real_time":""}
]


# TODO: set start_date using station['active_dates']?
with DAG(
    'ingest_nerrs',
    catchup=True,
    schedule_interval="0 0 * * 1",  # weekly
    max_active_runs=1,
    default_args={
        "start_date": datetime(2020, 1, 1),
        "retries": 5,
        "retry_delay": timedelta(days=60),
        "retry_exponential_backoff": True
    },
) as dag:
    for station in STATIONS:
        station_name = f"{station['reserve_name']}_{station['Station_Name']}".replace(' ', '_')
        # TODO: check if {{ds}} within the active_dates
        PythonOperator(
            task_id=f"ingest_nerrs_{station_name}_{station['Station_Code']}",
            python_callable=nerrs2influx,
            op_kwargs={
                'station_name': station_name,
                'station_code': station['Station_Code'],  # "acespwq"  # ace sp wq 
                'execution_date_str': '{{ ds }}',  # Pass the execution_date directly
                'active_dates': station['active_dates'],
                'exclude_params': ['MaxWSpdT']  # don't load this param
            }
        )
            