def dataframe_to_influx(dataframe, measurement, tags=[[]], fields=[["value", "Sal"]],
               timeCol='DateTimeStamp', should_convert_time=False):
    """
    Fetch data from an IMaRS gcloud bucket and upload it to InfluxDB.

    Parameters:
        dataframe (pandas.DataFrame) : df to send to influx
        measurement (str): InfluxDB measurement name.
        tags (list): List of [key, value] pairs for tags.
        fields (list): List of [csv_column, influx_field] pairs.
        timeCol (str): Name of the time column in the CSV.
        skiprows (int or list, optional): Rows to skip when reading the CSV.
        should_convert_time (bool): Whether to convert the time column to datetime.
    """
    import pandas as pd
    data = dataframe
    
    # Optionally convert the time column
    if should_convert_time:
        try:
            data[timeCol] = pd.to_datetime(data[timeCol])
            print("Converted time column to datetime")
        except Exception as e:
            print("Failed to convert time column:", e)
            raise e

    # === Upload the data to InfluxDB ===
    import influxdb_client, os
    from influxdb_client import InfluxDBClient, Point
    from influxdb_client.client.write_api import SYNCHRONOUS

    token = os.environ.get("INFLUXDB_TOKEN")
    org = "imars"
    url = os.environ.get("INFLUXDB_HOSTNAME")
    print('influx url: ', url)
    timeout = 600000  # 10min timeout
    client = influxdb_client.InfluxDBClient(url=url, token=token, org=org, timeout=timeout)
    bucket = "imars_bucket"
        
    # Write each point in the dataframe to InfluxDB
    points = []
    for index, row in data.iterrows():
        try: 
            point = (
                Point(measurement)
                .time(row[timeCol])
            )
            for field in fields:
                # field is a [csv_column, influx_field] pair
                point = point.field(field[1], row[field[0]])
            for tag in tags:
                # tag is a [key, value] pair
                point = point.tag(tag[0], tag[1])
            points.append(point)
        except KeyError as e:
            print(f"Column '{field[0]}' not found in CSV file")
            continue

    # Batch write points
    results = client.write_api(write_options=SYNCHRONOUS).write(bucket=bucket, org=org, record=points)
    
    if len(points) < 1:
        raise AssertionError("No points were uploaded")
    else:
        print(f"{len(points)} points written to db")

    # Manually close the client to ensure no batching issues
    client.__del__()
    print("InfluxDB API response:")
    print(results)
