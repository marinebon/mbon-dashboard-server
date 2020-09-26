# ============================================================================
# === usgs discharge data
# ============================================================================
import subprocess


def ts_ingest_script_usgs(BASE_DIRECTORY, UPLOADER_ROUTE, rivers):
    base_dir = BASE_DIRECTORY + '/DISCH_CSV_USGS'
    # 'USGS_disch_FKdb.csv'
    # 'USGS_disch_FWCdb_EFL.csv'
    for river in rivers:
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
