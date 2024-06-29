def csv2influx(data_url, measurement, tags=[], field=["value", "Sal"], timeCol='DateTimeStamp'):
    """
    fetch data from IMaRS gcloud bucket
    """
    import pandas as pd
    try: 
        data = pd.read_csv(data_url)
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
    
    client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
    bucket="imars_bucket"
        
    # write each point in the df to influxDB
    points = []
    for index, row in data.iterrows():
        print(f"{row['Sal']} @ {row['DateTimeStamp']}")
        point = (
            Point(measurement)
            .time(row[timeCol])  # not utc_timestamp ?
        )
        for key, val in fields:
            point = point.field(key, row[val])
        for key, val in tags:
            point = point.tag(key, val)
        points.append(point)
        
    # Batch write points
    results = client.write_api(write_options=SYNCHRONOUS).write(bucket=bucket, org=org, record=points)  
    # Manually close the client to ensure no batching issues
    client.__del__()
    print("influxdb API response:")
    print(results)
