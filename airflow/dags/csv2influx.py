#!/usr/bin/env python3
import argparse

from dataframe_to_influx import dataframe_to_influx

def csv2influx(data_url, measurement, tags=[[]], fields=[["value", "Sal"]],
               timeCol='DateTimeStamp', skiprows=None, should_convert_time=False):
    """
    Fetch data from an IMaRS gcloud bucket and upload it to InfluxDB.

    Parameters:
        data_url (str): URL or file path of the CSV data.
        measurement (str): InfluxDB measurement name.
        tags (list): List of [key, value] pairs for tags.
        fields (list): List of [csv_column, influx_field] pairs.
        timeCol (str): Name of the time column in the CSV.
        skiprows (int or list, optional): Rows to skip when reading the CSV.
        should_convert_time (bool): Whether to convert the time column to datetime.
    """
    import pandas as pd
    try: 
        data = pd.read_csv(data_url, skiprows=skiprows)
        print(f"loaded data cols: {data.columns}")
        print(f"1st few rows:\n{data.head()}")
    except Exception as e:
        print(f"failed to load data from {data_url}...\n", e)
        raise e

    dataframe_to_influx(data, measurement, tags, fields, timeCol, should_convert_time)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload CSV data to InfluxDB using the csv2influx function."
    )
    parser.add_argument("measurement", type=str,
                        help="InfluxDB measurement name (e.g., sofar_bouy)")
    parser.add_argument("--tag_set", type=str,
                        help="Tag set in the form key=value. For multiple tags, separate by commas (e.g., key1=val1,key2=val2)")
    parser.add_argument("--fields", type=str, required=True,
                        help="Fields as csv_field,influx_field. For multiple fields, separate pairs by commas "
                             "(e.g., value,sensor_position,temperature,temp)")
    parser.add_argument("--time_column", type=str, default="DateTimeStamp",
                        help="CSV time column name (default: DateTimeStamp)")
    parser.add_argument("--should_convert_time", action="store_true",
                        help="Convert the time column to datetime (default: False)")
    parser.add_argument("--file", type=str, required=True,
                        help="CSV file path. Prefix with '@' if providing a file path (e.g., @./datafile.csv)")
    
    args = parser.parse_args()

    # Process the file argument (remove '@' if present)
    data_url = args.file
    if data_url.startswith("@"):
        data_url = data_url[1:]
    
    # Process tag_set (if provided, expect a comma-separated list of key=value pairs)
    tags = []
    if args.tag_set:
        tag_list = args.tag_set.split(',')
        for tag in tag_list:
            if '=' not in tag:
                parser.error("Each tag in tag_set must be in the form key=value")
            key, value = tag.split('=', 1)
            tags.append([key, value])
    
    # Process fields (expect comma-separated pairs: csv_field,influx_field)
    field_list = args.fields.split(',')
    if len(field_list) % 2 != 0:
        parser.error("Fields must be provided as pairs: csv_field,influx_field")
    fields = [[field_list[i], field_list[i+1]] for i in range(0, len(field_list), 2)]
    
    csv2influx(data_url,
               measurement=args.measurement,
               tags=tags,
               fields=fields,
               timeCol=args.time_column,
               skiprows=None,
               should_convert_time=args.should_convert_time)
