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

from ts_ingest_script_bouys import ts_ingest_script_bouys
from ts_ingest_script_regions import ts_ingest_script_regions
from ts_ingest_script_usgs import ts_ingest_script_usgs

UPLOADER_HOSTNAME = os.environ["UPLOADER_HOSTNAME"]
if UPLOADER_HOSTNAME.endswith('/'):  # rm possible trailing /
    UPLOADER_HOSTNAME = UPLOADER_HOSTNAME[:-1]
UPLOADER_ROUTE = UPLOADER_HOSTNAME + "/submit/sat_image_extraction"

BASE_DIRECTORY = '/srv/imars-objects/fk'

ts_ingest_script_usgs(BASE_DIRECTORY, UPLOADER_ROUTE)

ts_ingest_script_regions(BASE_DIRECTORY, UPLOADER_ROUTE)

ts_ingest_script_bouys(BASE_DIRECTORY, UPLOADER_ROUTE)
