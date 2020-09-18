#!/bin/bash

# Ingests all timeseries .csv files into influxdb using mbon_data_uploader.
"""
This script submits all csv FK data to the mbon_data_uploader using curl.
It will take several minutes to complete.
This functions by sending the csv file and some metadata to the
mbon_data_uploader server, which inserts the data into influxdb.

The code here can be used as an example of how to submit data using curl.
Although a bash file might have been more informative, python is used here
for legibility as we loop across several lists and insert variables.

The curl queries here look something like the following:

```bash
curl \
    --form measurement=river_discharge \
    --form tag_set=location=river_name,source=usgs \
    --form fields=mean,climatology,anomaly \
    --form file=@csv_filepath_here \
    --form time_column=time \
    http://tylar-pc:5000/
```

If this script is successful you will see a redirect for each file that is
uploaded.
If a file fails you will receive an html response with the stack trace.
"""

import os
import subprocess
UPLOADER_HOSTNAME = os.environ["UPLOADER_HOSTNAME"]
if UPLOADER_HOSTNAME.endswith('/'):  # rm possible trailing /
    UPLOADER_HOSTNAME = UPLOADER_HOSTNAME[:-1]
UPLOADER_ROUTE = UPLOADER_HOSTNAME + "/submit/sat_image_extraction"


BASE_DIRECTORY = '/srv/imars-objects/fk'
# ============================================================================
# === usgs discharge data
# ============================================================================
base_dir = BASE_DIRECTORY + '/DISCH_CSV_USGS'
# 'USGS_disch_FKdb.csv'
# 'USGS_disch_FWCdb_EFL.csv'
for river in ['FKdb', 'FWCdb_EFL']:
    filepath = base_dir + '/USGS_disch_' + river + '.csv'
    subprocess.run([
        'curl',
        '--form', 'measurement=river_discharge',
        '--form', 'tag_set=location=' + river + ',source=usgs',
        '--form', 'fields=mean,climatology,anomaly',
        '--form', 'file=@' + filepath,
        '--form', 'time_column=time',
        # -H 'Content-Type: text/plain'
        # -u 'username:password'
        UPLOADER_ROUTE
    ], check=True)
# ============================================================================
# === Sat region extractions
# ============================================================================
FK_SUBREGIONS = [
    'BB', 'BIS', 'CAR', 'DT', 'DTN', 'EFB', 'EK_IN', 'EK_MID', 'FKNMS', 'FLB',
    'FROCK', 'IFB', 'KW', 'LK', 'MIA', 'MK', 'MOL', 'MQ', 'MR', 'MUK',
    'PBI', 'PEV', 'SANDK', 'SFP10', 'SFP11', 'SFP12', 'SFP13', 'SFP14',
    'SFP15_5', 'SFP15', 'SFP16', 'SFP17', 'SFP18', 'SFP19', 'SFP1', 'SFP20',
    'SFP21_5', 'SFP22_5', 'SFP22', 'SFP23', 'SFP24', 'SFP2', 'SFP30_5',
    'SFP31', 'SFP32', 'SFP33', 'SFP34', 'SFP39', 'SFP40', 'SFP41', 'SFP42',
    'SFP45', 'SFP46', 'SFP47', 'SFP48', 'SFP49', 'SFP4', 'SFP50', 'SFP51',
    'SFP52', 'SFP53', 'SFP54', 'SFP5_5', 'SFP55', 'SFP56', 'SFP57_2',
    'SFP57_3', 'SFP57', 'SFP5', 'SFP61', 'SFP62', 'SFP63', 'SFP64', 'SFP6_5',
    'SFP61', 'SFP62', 'SFP63', 'SFP64', 'SFP6_5', 'SFP65', 'SFP66', 'SFP67',
    'SFP69', 'SFP6', 'SFP70', 'SFP7', 'SFP8', 'SFP9_5', 'SFP9', 'SUG', 'SLI',
    'SOM', 'SR', 'UFB1', 'UFB2', 'UFB4', 'UK', 'UK_IN', 'UK_MID', 'UK_OFF',
    'WFB', 'WFS', 'WS'
]
# === MODA
base_dir = BASE_DIRECTORY + '/EXT_TS_MODA/OC/'
for roi in FK_SUBREGIONS:
    filepath = base_dir + '/FKdbv2_ABI_TS_MODA_daily_' + roi + '.csv'
    subprocess.run([
        'curl',
        '--form', 'measurement=modis_abi',
        '--form', 'tag_set=location=' + roi + ',sensor=modis',
        '--form', 'fields=mean,climatology,anomaly',
        '--form', 'file=@' + filepath,
        '--form', 'time_column=Time',
        # -H 'Content-Type: text/plain'
        # -u 'username:password'
        UPLOADER_ROUTE
    ], check=True)


# EXT_TS_MODA/SST & SST4 are empty (2020-07-09)


# === VIIRS
base_dir = BASE_DIRECTORY + '/EXT_TS_VSNPP/OC/'
for roi in FK_SUBREGIONS:
    for product in ["chlor_a", "Kd_490", "Rrs_671"]:
        filepath = (
            base_dir + '/FKdbv2_' + product + '_TS_VSNPP_daily_' + roi + '.csv'
        )
        subprocess.run([
            'curl',
            '--form', 'measurement=viirs_' + product.lower(),
            '--form', 'tag_set=location=' + roi + ',sensor=viirs',
            '--form', 'fields=mean,climatology,anomaly',
            '--form', 'file=@' + filepath,
            '--form', 'time_column=Time',
            # -H 'Content-Type: text/plain'
            # -u 'username:password'
            UPLOADER_ROUTE
        ], check=True)

# EXT_TS_VSNPP/SST is empty

base_dir = BASE_DIRECTORY + '/EXT_TS_VSNPP/SSTN/'
for roi in FK_SUBREGIONS:
    filepath = base_dir + '/FKdbv2_sstn_TS_VSNPP_daily_' + roi + '.csv'
    subprocess.run([
        'curl',
        '--form', 'measurement=viirs_sstn',
        '--form', 'tag_set=location=' + roi + ',sensor=viirs',
        '--form', 'fields="mean,climatology,anomaly"',
        '--form', 'file=@' + filepath,
        '--form', 'time_column=Time',
        # -H 'Content-Type: text/plain'
        # -u 'username:password'
        UPLOADER_ROUTE
    ], check=True)


# === FK bouys
base_dir = '/srv/imars-objects/fk/SAL_TS_NDBC'
for roi in ['BUTTERNUT', 'WHIPRAY', 'PETERSON', 'BOBALLEN', 'LITTLERABBIT']:
    for product in ['sal', 'temp']:
        filepath = base_dir + '/' + roi + '_NDBC_' + product + '_FKdb.csv'
        result = subprocess.run([
            'curl',
            '--form', 'measurement=bouy_' + product,
            '--form', 'tag_set=location=' + roi + ',source=ndbc',
            '--form', 'fields="mean,climatology,anomaly"',
            '--form', 'file=@' + filepath,
            '--form', 'time_column=time',
            # -H 'Content-Type: text/plain'
            # -u 'username:password'
            UPLOADER_ROUTE
        ], check=True)
        print(result.args)
