"""
Ingest bouy data 
"""
import os

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

DATA_HOST = "https://raw.githubusercontent.com/7yl4r/extracted_sat_ts_gom_csv_data/main/data"

# ============================================================================
# === DAG defines the task exec order
# ============================================================================
with DAG(
    'sofar_ingest',
    catchup=True,
    schedule_interval="0 0 * * *",
    max_active_runs=1,
    default_args={
        "start_date": datetime(2023, 6, 20)
    },
) as dag:
    UPLOADER_HOSTNAME = os.environ["UPLOADER_HOSTNAME"]
    if UPLOADER_HOSTNAME.endswith('/'):  # rm possible trailing /
        UPLOADER_HOSTNAME = UPLOADER_HOSTNAME[:-1]
    UPLOADER_ROUTE = UPLOADER_HOSTNAME + "/submit/sat_image_extraction"
    BashOperator(
        task_id=f"sofar_ingest",
        bash_command=(
            "curl 'https://api.sofarocean.com/fetch/download-sensor-data/?spotterId=SPOT-30987C&startDate={{ prev_ds }}T{{ ts }}Z&endDate={{ ds }}T{{ ts }}Z&processingSources=all' "
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
            " && curl --location --fail-with-body "
            "    --form measurement=sofar_bouy "
            "    --form tag_set=spotter_id=SPOT30987C "
            "    --form fields=value,sensor_position "
            "    --form time_column=utc_timestamp "
            "    --form file=@./datafile.csv "
            "    {{params.uploader_route}} "
        ),
        params={
            'uploader_route': UPLOADER_ROUTE,
        }
    )
