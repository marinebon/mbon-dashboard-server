def csv2influx(data_url, measurement, tags=[[]], fields=[["value", "Sal"]], timeCol='DateTimeStamp', skiprows=None):
    """
    fetch data from IMaRS gcloud bucket
    """
    import pandas as pd
    try: 
        data = pd.read_csv(data_url, skiprows=skiprows)
        print(f"loaded data cols: {data.columns}")
        print(f"1st few rows:\n {data.head()}")
    except Exception as e:
        print(f"failed to `getData({data_url})`...\n", e)
        raise e
        
    # === upload the data
    # influx connection setup
    import influxdb_client, os, time
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    
    token = os.environ.get("INFLUXDB_TOKEN")
    org = "imars"
    url = os.environ.get("INFLUXDB_HOSTNAME")
    
    client = influxdb_client.InfluxDBClient(url=url, token=token, org=org, timeout=(60*1000))
    bucket="imars_bucket"
        
    # write each point in the df to influxDB
    points = []
    for index, row in data.iterrows():
        #print(f"{row}")
        point = (
            Point(measurement)
            .time(row[timeCol])  # not utc_timestamp ?
        )
        for field in fields:
            point = point.field(field[1], row[field[0]])
        for tag in tags:
            point = point.tag(tag[0], tag[1])
        points.append(point)
        
    # Batch write points
    results = client.write_api(write_options=SYNCHRONOUS).write(bucket=bucket, org=org, record=points)  
    # Manually close the client to ensure no batching issues
    client.__del__()
    print("influxdb API response:")
    print(results)
