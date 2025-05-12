'''
NOTE: this function is unused!

grab buoy data from NDBC and ingest to influxDB.
'''

def ndbc_to_influx(ds, **op_kwargs):
    """
    Downloads the NDBC historical stdmet file for station_name at year=ds-1,
    parses it into a DataFrame with a datetime column, and then calls csv_to_influx().
    Requires provide_context=True on the PythonOperator so that `ds` is injected.
    """
    # 1) year = params.ds - 1yr
    #    ds comes in as 'YYYY-MM-DD'
    year = int(ds.split('-')[0]) - 1
    op_kwargs['year'] = year

    # 2) grab & uncompress data from
    data_url = (
        f"https://www.ndbc.noaa.gov/data/historical/stdmet/"
        f"{op_kwargs['buoy_id']}{year}.txt.gz"
    )
    resp = requests.get(data_url)
    resp.raise_for_status()

    # 3) uncompress into a file-like object
    compressed = io.BytesIO(resp.content)
    with gzip.GzipFile(fileobj=compressed) as gz:
        # 4) load as DataFrame: skip the 2nd header row (units) and drop any comment lines
        df = pd.read_csv(
            gz,
            delim_whitespace=True,
            skiprows=[1],      # drop the units line
            #comment='#'        # skip any other comment lines
        )
        # first column (YY) gets read in with # prepended (#YY)
        df['YY'] = df['#YY']

    pandas.set_option('display.max_columns', None)
    print('df.head:', df.head())
    # 5) add 'datetime' column using YY, MM, DD, hh, mm
    #    First build a 4-digit year column
    df['datetime'] = pd.to_datetime({
        'year':   df['YY'],
        'month':  df['MM'],
        'day':    df['DD'],
        'hour':   df['hh'],
        'minute': df['mm']
    })

    # override the time column name for csv_to_influx
    op_kwargs['dataframe'] = df
    op_kwargs['timeCol'] = 'datetime'


    print('kwargs:', op_kwargs)
    #    def dataframe_to_influx(dataframe, measurement, tags=[[]], fields=[["value", "Sal"]],
    #               timeCol='DateTimeStamp', should_convert_time=False):
    # finally hand off to your generic CSV→Influx helper
    dataframe_to_influx(
        df,
        op_kwargs['measurement'],
        op_kwargs['tags'],
        op_kwargs['fields'],
        op_kwargs['timeCol'],
        #op_kwargs['should_convert_time']
    )


''' example usage:

with DAG(
    'ingest_oa',
    catchup=True,  # latest only
    schedule_interval="@yearly",
    max_active_runs=2,
    default_args={
        "start_date": datetime(2020, 2, 1)  # 1 month delay for NDBC to publish last year's data
    },
) as dag:

    #YY  MM DD hh mm WDIR WSPD GST  WVHT   DPD   APD MWD   PRES  ATMP  WTMP  DEWP  VIS  TIDE
    PARAM_LIST = {
        'ApCo2': 'pco2_in_air',
        'Sal': 'sea_water_practical_salinity',
        'WTemp': 'sea_water_temperature',
        'WpCo2': 'pco2_in_sea_water',
        'pH': 'sea_water_ph_reported_on_total_scale',
    }
    for param_name, param_col_name in PARAM_LIST.items():
        FPATH = f"gov_ornl_cdiac_graysrf_{param_name}.csv"
        PythonOperator(
            task_id=f"ingest_oa_{param_name}",
            python_callable=ndbc_to_influx,
            provide_context=True,
            op_kwargs={
                'buoy_id': '41008h',
                'measurement': 'oa_params',
                'fields': [
                    [param_col_name, param_name]
                ],
                'skiprows': [1],  # skip 2nd header row (units)
                'tags': ["source", "ORNL_OA"],
                'timeCol':'time'
            }
        )
'''
