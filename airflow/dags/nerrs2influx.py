# ingest from NERRS CDMO.
# NOTE: data access requires registration.
#       See details https://cdmo.baruch.sc.edu/webservices.cfm

from datetime import datetime, timedelta
import pandas as pd
import pendulum # for date parsing

from airflow.exceptions import AirflowSkipException
import nerrs_data
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


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

        
def is_ds_within_active_dates(active_dates, ds):
    # check if the datetime of the dag is within the active dates
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
            return True
    else:
        return False

    
def nerrs2influx(station_name, station_code, execution_date_str, active_dates, exclude_params=[]):
    """
    fetch met data based on docs from https://cdmo.baruch.sc.edu/webservices.cfm
    """
    #print(f'ds: {execution_date_str}')
    # Convert the execution_date_str to a datetime object to get end_date
    execution_date = datetime.strptime(execution_date_str, '%Y-%m-%d')
    #print(f'dt: {execution_date}')
    end_date_str = (execution_date + timedelta(days=7)).strftime('%Y-%m-%d')
    if(not is_ds_within_active_dates(active_dates, execution_date_str)):
        raise AirflowSkipException(f"Date range ouside of active dates {active_dates}")
    print(f'Active dates {active_dates} cover this date range.')
    print(f'loading {execution_date_str} / {end_date_str}...') 
    try:
        param_data = nerrs_data.exportAllParamsDateRange(station_code, execution_date_str, end_date_str)
        #print(f"loaded data cols: {param_data.columns}")
        pd.set_option('display.max_columns', None)  # Show all columns
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

    points = []
    for index, row in param_data.iterrows():
        point = (
            Point("nerrs")
            .tag("station_code", station_code)
            .tag("location", station_name)
            .tag("source", "NERRS_CDMO")
            .time(row['DateTimeStamp'])
        )
        for colName in param_data.columns:
            if colName not in skipColumns:
                try:
                    point = point.field(colName, float(row[colName]))
                except TypeError as err:  # catch NoneType values
                    print(f"{colName} value is not float: {row[colName]}", end="|")
                except ValueError as err:  # catch string values
                    print(f"{colName} value is non-coerceable string: {row[colName]}", end="|")
        points.append(point)
    print("\n")
    # batch write points
    results = client.write_api(write_options=SYNCHRONOUS).write(
        bucket=bucket, org=org, record=points
    )
    print(f"{len(points)} points submitted")
    # Manually close the client to ensure no batching issues
    client.__del__()
    print("influxdb API response:")
    print(results)  
