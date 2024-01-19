The process of getting `csv` files into the dashboard is a bit complex.
For testing purposes a csv can be uploaded manually using the web form provided by mbon_uploader.
To automate the ingest of a `csv`, the `.csv` needs to be made available over http, then an airflow job can be set up to grab the csv and upload it using curl.

In the past we pushed csvs in to github.
Currently we are pushing csv files into a google cloud bucket using the `gsutil` command on on an IMaRS server (dotis@manglillo).
