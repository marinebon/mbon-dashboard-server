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
        try: 
            param_data = nerrs_data.getData(station_code, product)
            print(f"loaded data cols: {param_data.columns}")
            print(f"1st few rows:\n {param_data.head()}")
        except Exception as e:
            print(f"failed to `getData({station_code}, {product})`...\n", e)
            raise e
        
        # === upload the data
        # influx connection setup
        import influxdb_client, os, time
        from influxdb_client import InfluxDBClient, Point, WritePrecision
        from influxdb_client.client.write_api import SYNCHRONOUS
        
        token = os.environ.get("INFLUXDB_TOKEN")
        org = "imars"
        url = os.environ.get("INFLUXDB_HOSTNAME")
        
        client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
        bucket="imars-bucket"
        
        # write each point in the df to influxDB
        points = []
        for index, row in param_data.iterrows():
            point = (
                Point(f"{suite}_{product}")
                .tag("station_code", station_code)
                .tag("location", station_name)
                .tag("sensor", suite)
                .field("value", row["Sal"])  # not row[product] ?
                .time(row['DateTimeStamp'])  # not utc_timestamp ?
            )
            points.append(point)
        
        # Batch write points
        results = client.write_api(write_options=SYNCHRONOUS).write(bucket=bucket, org=org, record=points)  
        # Manually close the client to ensure no batching issues
        client.__del__()
        print("influxdb API response:")
        print(results)
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
                    station_code = f"{nerr_abbrev}{station_abbrev}{suite}"
                    PythonOperator(
                        task_id=f"ingest_nerr_{suite}_{product}_{station_name}",
                        python_callable=nerrs2influx,
                        op_kwargs={
                            'station_name': station_name,
                            'station_code': station_code,  # "acespwq"  # ace sp wq
                            'suite': suite,
                            'product': product # "Sal"
                        },
                    )

