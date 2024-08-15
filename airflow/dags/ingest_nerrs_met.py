"""
Ingest NERRS met data.
Instrumented records (continuous, but only from one location at each NERR)

```mermaid
"NERRS CDMO" 
  -- "airflow ingest_nerr_met" --> influxDB 
"""
import os

from airflow import DAG
from airflow.operators.python_operator import BranchPythonOperator, PythonOperator
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup
from datetime import datetime, timedelta
import pendulum  # for date parsing

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


def parse_date(date_str):
    try:
        # Try to parse with a more lenient setting
        parsed_date = pendulum.parse(date_str.strip(), strict=False)
        return parsed_date
    except pendulum.parsing.exceptions.ParserError:
        # Handle partial dates like "Aug 2004" by adding the first day of the month
        try:
            return pendulum.from_format(date_str.strip(), 'MMM YYYY')
        except pendulum.parsing.exceptions.ParserError:
            print(f"Failed to parse date: {date_str}. Please check the format.")
            return None

def is_ds_within_active_dates(active_dates, group_id, **kwargs):
    # check if the datetime of the dag is within the active dates
    ds = kwargs['ds']  # Extract 'ds' from kwargs
    ds_date = pendulum.parse(ds)

    for period in active_dates.split(';'):
        start_str, end_str = period.split('-')

        start_date = parse_date(start_str)
        if start_date is None:
            continue

        # If the end date is not provided, assume it to be today or a future date
        if end_str.strip():
            end_date = parse_date(end_str)
            if end_date is None:
                continue
        else:
            end_date = pendulum.now()

        if start_date <= ds_date <= end_date:
            return f"{group_id}.run"
    else:
        return f"{group_id}.skip"

with DAG(
    'ingest_nerrs_met',
    catchup=True,
    schedule_interval="0 0 * * 1",  # weekly
    max_active_runs=1,
    default_args={
        "start_date": datetime(2020, 1, 1)
    },
) as dag:
    for station in STATIONS:
        station_name = station['Station_Name'].replace(' ', '_')
        station_code = station['Station_Code']
        active_dates = station['active_dates']
        group_id = f"ingest_{station_code}"
        with TaskGroup(group_id=group_id) as group:

            branch_task = BranchPythonOperator(
                task_id=f"branch",
                python_callable=is_ds_within_active_dates,
                op_args=[active_dates, group_id],
                provide_context=True  # for ds
            )

            skip_task_op = PythonOperator(
                task_id=f"skip",
                python_callable=lambda: print(f'skipped. timeframe outside of {active_dates}')
            )
            
            run_task_op = PythonOperator(
                task_id=f"run",
                python_callable=nerrs2influx,
                op_kwargs={
                    'station_name': station_name,
                    'station_code': station['Station_Code'],  # "acespwq"  # ace sp wq 
                    'execution_date_str': '{{ ds }}',  # Pass the execution_date directly
                    'exclude_params': ['MaxWSpdT'],  # don't load this param
                    'active_dates': active_dates
                }
            )

            branch_task >> [skip_task_op, run_task_op]

            
