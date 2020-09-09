#!/bin/bash
"""
This script queries FWC's ArcGIS portal for data.
"""

import os
import requests

from influxdb import InfluxDBClient

INFLUXDB_HOSTNAME = os.environ["INFLUXDB_HOSTNAME"]
INFLUXDB_PORT = os.environ["INFLUXDB_PORT"]
INFLUXDB_USERNAME = os.environ["INFLUXDB_USERNAME"]
INFLUXDB_PASSWORD = os.environ["INFLUXDB_PASSWORD"]
INFLUXDB_DB = os.environ["INFLUXDB_DB"]

response = requests.post(
    "https://services2.arcgis.com/z6TmTIyYXEYhuNM0/arcgis/rest/services/"
    "Coral_Disease_Boundary/FeatureServer/0/query?"
    "f=json&where=1=1&"
    "outSr=4326&"
    "outFields=Date_Obs,SCTLD_Present,Site_Name"
)

"""
Example of expected response:
{
    "features": [
        {
            "attributes": {
                "Date_Obs": 1577941200000,
                "SCTLD_Present": "Yes",
                "Site_Name": "B-5"
            },
            "geometry": {
                "x": -81.38171,
                "y": 24.55261999999999
            }
        },
    ]
}
"""
assert response.status_code == 200
data = response.json()

rows = []
for feature in data["features"]:
    rows.append(
        {
            "measurement": "SCTLD_Present",
            "tags": {
                "Site_Name": feature['attributes']["Site_Name"],
                "latitude": feature['geometry']['x'],
                "longitude": feature['geometry']['y'],
            },
            "time": feature['attributes']["Date_Obs"]*1000000,
            "fields": {
                "value": (
                    1 if feature['attributes']['SCTLD_Present'] == "Yes" else 0
                )
            }
        }
    )
client = InfluxDBClient(
    INFLUXDB_HOSTNAME, INFLUXDB_PORT,
    INFLUXDB_USERNAME, INFLUXDB_PASSWORD,
    INFLUXDB_DB
)
client.write_points(rows)

print(f'{len(rows)} rows inserted')

import pdb; pdb.set_trace()
