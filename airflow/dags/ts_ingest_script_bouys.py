# === FK bouys
import subprocess


def ts_ingest_script_bouys(BASE_DIRECTORY, UPLOADER_ROUTE):
    base_dir = BASE_DIRECTORY + '/SAL_TS_NDBC'
    for roi in [
        'BUTTERNUT', 'WHIPRAY', 'PETERSON', 'BOBALLEN', 'LITTLERABBIT'
    ]:
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
