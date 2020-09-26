# ============================================================================
# === Sat region extractions
# ============================================================================
import subprocess


def ts_ingest_script_regions(
    BASE_DIRECTORY, UPLOADER_ROUTE, SUBREGIONS, file_name_pattern
):
    # === MODA
    base_dir = BASE_DIRECTORY + '/EXT_TS_MODA/OC/'
    for roi in SUBREGIONS:
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
    for roi in SUBREGIONS:
        for product in ["chlor_a", "Kd_490", "Rrs_671"]:
            filepath = (
                base_dir + file_name_pattern.format(product=product, roi=roi)
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
    for roi in SUBREGIONS:
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
