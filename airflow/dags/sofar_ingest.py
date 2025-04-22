"""
Ingest SOFAR bouy data. 
"""
import os

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

# NOTE: This is not working.
#       Data is ingested but cannot be subset by sensor_position.
#       Need to modify so that sensor_position column can be used as a
#       tag.
with DAG(
    'sofar_ingest',
    catchup=True,
    schedule_interval="0 0 * * *",
    max_active_runs=4,
    default_args={
        "start_date": datetime(2023, 6, 20),
        'retries': 3,
        'retry_delay': timedelta(days=1),
    },
) as dag:    
    BashOperator(
        task_id=f"sofar_ingest",
        bash_command=(
            "curl 'https://api.sofarocean.com/fetch/download-sensor-data/"
            "?spotterId=SPOT-30987C"
            "&startDate={{ prev_ds }}T00:00Z"
            "&endDate={{ ds }}T00:00Z"
            "&processingSources=all' "
            "  -X GET "
            "  -H 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0' "
            "  -H 'Accept: application/json, text/plain, */*' "
            "  -H 'Accept-Language: en-US,en;q=0.5' "
            "  -H 'Content-Type: application/x-www-form-urlencoded' "
            "  -H 'view_token: 1bc9848d3e524c34a1eb220e121d9a9e' "
            "  -H 'Sec-Fetch-Dest: empty' "
            "  -H 'Sec-Fetch-Mode: cors' "
            "  -H 'Sec-Fetch-Site: same-site' "
            "  -H 'Pragma: no-cache' "
            "  -H 'Cache-Control: no-cache' "
            "  -H 'referrer: https://spotters.sofarocean.com/' "
            "  -H 'credentials: omit' "
            "  -H 'mode: cors' "
            "  > datafile.csv "
            " && head datafile.csv "
            " && python /opt/airflow/dags/csv2influx.py "
            "    sofar_bouy "
            " --tag_set "
            " spotter_id=SPOT30987C,sensor_position=999 "  # TODO: how to get sensor_position from file here
            " --fields value,sofar_temperature "
            " --time_column utc_timestamp "
            " --should_convert_time "
            " --file "
            " @./datafile.csv "
        ),
        params={
        }
    )
