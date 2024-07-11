import pandas as pd

import nerrs_data
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

def nerrs2influx(station_name, station_code, suite, product):
    """
    fetch met data based on docs from https://cdmo.baruch.sc.edu/webservices.cfm
    """
    try:
        RECORDS_PER_DAY = 96 # 24hrs * 60min/hr * 1sample/15min
        param_data = nerrs_data.exportSingleParam(station_code, product, n_records=RECORDS_PER_DAY)
        print(f"loaded data cols: {param_data.columns}")
        print(f"1st few rows:\n {param_data.head()}")
    except Exception as e:
        print(f"failed `exportSingleParam({station_code}, {product})`\n", e)
        raise e
        
    # === upload the data
    # influx connection setup
        
    token = os.environ.get("INFLUXDB_TOKEN")
    org = "imars"
    url = os.environ.get("INFLUXDB_HOSTNAME")
        
    client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
    bucket="imars_bucket"
        
    # write each point in the df to influxDB
    points = []
    for index, row in param_data.iterrows():
        #print(f"{row[product]} @ {row['DateTimeStamp']}")
        point = (
            Point(f"{suite}_{product}")
            .tag("station_code", station_code)
            .tag("location", station_name)
            .tag("sensor", suite)
            .field(product, row[product])
            .time(row['DateTimeStamp'])
        )
        points.append(point)

    # Batch write points
    results = client.write_api(write_options=SYNCHRONOUS).write(bucket=bucket, org=org, record=points)  
    # Manually close the client to ensure no batching issues
    client.__del__()
    print("influxdb API response:")
    print(results)  
