from datetime import datetime, timedelta
import pandas as pd

import nerrs_data
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

def nerrs2influx(station_name, station_code, execution_date_str, active_dates, exclude_params=[]):
    """
    fetch met data based on docs from https://cdmo.baruch.sc.edu/webservices.cfm
    """
    #print(f'ds: {execution_date_str}')
    # Convert the execution_date_str to a datetime object to get end_date
    execution_date = datetime.strptime(execution_date_str, '%Y-%m-%d')
    #print(f'dt: {execution_date}')
    end_date_str = (execution_date + timedelta(days=7)).strftime('%Y-%m-%d')
    print(f'Active dates {active_dates} cover this date range.')
    print(f'loading {execution_date_str} / {end_date_str}...') 
    try:
        param_data = nerrs_data.exportAllParamsDateRange(station_code, execution_date_str, end_date_str)
        #print(f"loaded data cols: {param_data.columns}")
        print(f"1st few rows:\n {param_data.head()}")
    except Exception as e:
        print(f"failed `exportSingleParam({station_code})`\n", e)
        raise e
        
    # === upload the data
    # influx connection setup
        
    token = os.environ.get("INFLUXDB_TOKEN")
    org = "imars"
    url = os.environ.get("INFLUXDB_HOSTNAME")
        
    client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
    bucket="imars_bucket"

    # TODO: rewrite this to work with new datastruct
    # === write each point in the df to influxDB
    skipColumns = [
        'ID', 'Historical', 'DateTimeStamp', 'MarkAsDeleted','ProvisionalPlus',
        'utcStamp'
    ] + exclude_params
    #print(f'loading {param_data.columns} minus {skipColumns}')
    for colName in param_data.columns:
        # TODO: skip if startswith('EC_') ?
        if colName not in skipColumns:
            print(colName)
            points = []
            for index, row in param_data.iterrows():
                print(f"{row[colName]} @ {row['DateTimeStamp']}")
                point = (
                    Point(colName)
                    .tag("station_code", station_code)
                    .tag("location", station_name)
                    .field(colName, row[colName])
                    .time(row['DateTimeStamp'])
                )
                points.append(point)
            # Batch write points
            results = client.write_api(write_options=SYNCHRONOUS).write(
                bucket=bucket, org=org, record=points
            )  
    # Manually close the client to ensure no batching issues
    client.__del__()
    print("influxdb API response:")
    print(results)  
