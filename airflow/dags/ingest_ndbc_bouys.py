# ingest_ndbc.py
"""
NDBC data ingested through SECOORA ERDDAP.
Data could also be grabbed directly from NDBC using methods in airflow/dags/ndbc_to_influx.py.

NDBC data is published annually. 
SECOORA publishes data in near-real-time.

start_date for buoy data should be 2015.

SECOORA ERDDAP URL format:
    https://erddap.secoora.org/erddap/tabledap/
        gov-nps-ever-{name}.csv?
        time%2C
        {param_name_1}%2C
        {param_name_2}%2C
        ...

Example URL for SECOORA ERDDAP:
    https://erddap.secoora.org/erddap/tabledap/gov-nps-ever-mdkf1.csv?time%2Csea_water_temperature%2Csea_water_practical_salinity
    https://erddap.secoora.org/erddap/tabledap/gov-nps-ever-wrbf1.csv?time%2Csea_water_practical_salinity&time%3E=2025-11-01&time%3C=2026-03-26T16%3A06%3A00Z

SECOORA data file example:
    time,                sea_water_temperature,sea_water_practical_salinity
    UTC,                 degree_Celsius,       1e-3
    2000-01-01T05:00:00Z,NaN,                  19.9761
    2000-01-01T05:15:00Z,NaN,                  20.0186


"""
import os
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

from csv2influx import csv2influx


INWATER_PARAMS = [
    "sea_water_practical_salinity", "sea_water_temperature"
]

NDBC_STATIONS = {  
    # TODO: could query ERDDAP to get list of params
'GOM': [
    {   
        "name": "bkyf1", "long_name": "Buoy_Key",
        "params": INWATER_PARAMS
    },{
        "name": "bnkf1", "long_name": "Butternut_Kay",
        "params": INWATER_PARAMS
    },{
        "name": "bobf1", "long_name": "Bob_Allen_Key",
        "params": INWATER_PARAMS
    },{
        "name": "bwsf1", "long_name": "Blackwater_Sound",
        "params": INWATER_PARAMS
    },{
        "name": "dkkf1", "long_name": "Duck_Key",
        "params": INWATER_PARAMS
    },{
        "name": "gbtf1", "long_name": "Garfield_Bight",
        "params": INWATER_PARAMS
    },{
        "name": "hcef1", "long_name": "Highway_Creek",
        "params": INWATER_PARAMS
    },{
        "name": "jbyf1", "long_name": "Joe_Bay",
        "params": INWATER_PARAMS
    },{
        "name": "jkyf1", "long_name": "Johnson_Key",
        "params": INWATER_PARAMS
    },{
        "name": "lbsf1", "long_name": "Little_Blackwater_Sound",
        "params": INWATER_PARAMS
    },{
        "name": "lmdf1", "long_name": "Little_Madeira_Bay",
        "params": INWATER_PARAMS
    },{
        "name": "lrkf1", "long_name": "Little_Rabbit_Key",
        "params": INWATER_PARAMS
    },{
        "name": "lsnf1", "long_name": "Long_Sound",
        "params": INWATER_PARAMS
    },{
        "name": "mdkf1", "long_name": "Middle_Key",
        "params": INWATER_PARAMS
    },{
        "name": "mukf1", "long_name": "Murray_Key",
        "params": INWATER_PARAMS
    },{
        "name": "pkyf1", "long_name": "Peterson_Key",
        "params": INWATER_PARAMS
    },{
        "name": "tbyf1", "long_name": "Terrapin_Bay",
        "params": INWATER_PARAMS
    },{
        "name": "thrf1", "long_name": "Thursday_Point",
        "params": INWATER_PARAMS
    },{
        "name": "wrbf1", "long_name": "Whipray_Basin",
        "params": INWATER_PARAMS
    },
    # NOTE: what about 
    #                  "Manatee_Bay",
    #                  "Taylor_River",
    #                  "Trout_Cove",
],
# NOTE: what about SEUS? Are these in ERDDAP or can they only come from NDBC directly?
#   "Grays_Reef",
#   "Fernandina",
#   "Charleston"
}

with DAG(
    'ingest_ndbc_buoys',
    catchup=False,  # latest only
    schedule_interval="0 14 * * *",
    max_active_runs=2,
    concurrency=20,
    default_args={
        "start_date": datetime(2015, 1, 1)
    },
) as dag:
    # Use Airflow Jinja macros to dynamically get times
    start_time = "{{ (execution_date - macros.timedelta(hours=25)).strftime('%Y-%m-%dT%H:%M:%SZ') }}"
    end_time = "{{ execution_date.strftime('%Y-%m-%dT%H:%M:%SZ') }}"
    for region, list_of_stations in NDBC_STATIONS.items():
        for station_data in list_of_stations:
            short_name = station_data['name']
            long_name = station_data['long_name']
            params = station_data['params']
            location_tag = f"{long_name} ({short_name[:-2]})"  # the -2 drops the f1 from the end of name
            
            for param in params:
                # Build the data URL for the SECOORA ERDDAP.
                # TODO: need to add time to URL
                url = f"https://erddap.secoora.org/erddap/tabledap/gov-nps-ever-{short_name}.csv?time%2C{param}&time%3E={start_time}&time%3C={end_time}"
                                                                                                
                
                # TODO: should we filter using qc?
                #       Need to add qc columns to url.
                #       {param}_qc_agg
                #       {param}_qs_tests          

                PythonOperator(
                    task_id=f"{region}_{short_name}_{param}",
                    python_callable=csv2influx,
                    op_kwargs={
                        'data_url': url,
                        'measurement': 'ndbc_buoy',
                        'fields': [[param, param]],
                        'tags': [
                            ['location', location_tag],
                            ['source', 'NDBC'],
                            ['region', region],
                        ],
                        'timeCol': 'time',
                        'skiprows': [1]
                    },
                )



# # //////////////////////////////////////////////////////////////////////////
# # DELETE BELOW HERE


# MET_PARAMS = [  # parameters published by NDBC in stdmet files
#     'air_pressure_at_mean_sea_level', 'air_temperature',
#     'sea_surface_temperature', 'wind_speed',
#     'wind_from_direction', 'wind_speed_of_gust',
#     'sea_surface_wave_significant_height',
#     'sea_surface_wave_mean_period',
#     'sea_surface_wave_from_direction',
#     'sea_surface_wave_period_at_variance_spectral_density_maximum'
# ]

# WATER_PARAMS = [  # parameters published by NDBC in water temp/salinity files
#     "sea_water_temperature",
#     "sea_water_practical_salinity"
# ]

# # Define a data structure similar to the satellite ingestion file.
# NDBC_DB_FILES = {
#     'GOM': {
#         'stations': [
#             "Trout_Cove"
#         ],
#         'datasets': {
#             'salinity': {
#                 'filename_template': "{station}_Buoy_WTMP_SAL.csv",
#                 'measurement': "salinity",
#                 'fields': [
#                     ["sea_water_temperature", "sea_water_temperature"],
#                     ["sea_water_practical_salinity", "sea_water_practical_salinity"]
#                 ],
#                 'tags': [
#                     ['source', 'NDBC']
#                 ],
#                 'timeCol': "time",
#                 'skiprows': [1]  # skip 2nd header row
#             }
#         }
#     },
#     'SEUS': {
#         'stations': [
#             "Grays_Reef",
#             "Fernandina",
#             "Charleston"
#         ],
#         'datasets': {
#             'meteorology': {
#                 'filename_template': "{station}_Buoy_STDMET.csv",
#                 'measurement': "meteorology",
#                 'fields': [
#                     [param, param] for param in MET_PARAMS
#                 ],
#                 'tags': [],
#                 'timeCol': "time",
#                 'skiprows': [1]  # skip 2nd header row
#             }
#         }
#     }
# }




# with DAG(
#     'ingest_ndbc_buoys_old',
#     catchup=False,  # latest only
#     schedule_interval="0 15 * * *",
#     max_active_runs=2,
#     default_args={
#         "start_date": datetime(2020, 1, 1)
#     },
# ) as dag:
#     for region, data in NDBC_DB_FILES.items():
#         # Set a region-specific bucket URL as in ingest_sat_ts.py.
#         GBUCKET_URL_PREFIX = f"https://storage.googleapis.com/{region.lower()}_csv"
#         for station in data['stations']:
#             for dataset_name, ds in data['datasets'].items():
#                 # Build the filename from the template.
#                 DATA_FNAME = ds['filename_template'].format(station=station)
#                 task_id = f"{region}_{dataset_name}_{station}"
#                 # Add the dynamic tag for location.
#                 tags = ds.get('tags', []) + [['location', station]]
#                 PythonOperator(
#                     task_id=task_id,
#                     python_callable=csv2influx,
#                     op_kwargs={
#                         'data_url': f"{GBUCKET_URL_PREFIX}/{DATA_FNAME}",
#                         'measurement': ds['measurement'],
#                         'fields': ds['fields'],
#                         'tags': tags,
#                         'timeCol': ds['timeCol'],
#                         'skiprows': ds.get('skiprows', [])
#                     },
#                 )
