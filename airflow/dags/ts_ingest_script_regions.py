# ============================================================================
# === Sat region extractions
# ============================================================================
import subprocess


def ts_ingest_script_regions(BASE_DIRECTORY, UPLOADER_ROUTE):
    FK_SUBREGIONS = [
        'BB', 'BIS', 'CAR', 'DT', 'DTN', 'EFB', 'EK_IN', 'EK_MID', 'FKNMS',
        'FLB', 'FROCK', 'IFB', 'KW', 'LK', 'MIA', 'MK', 'MOL', 'MQ', 'MR',
        'MUK', 'PBI', 'PEV', 'SANDK', 'SFP10', 'SFP11', 'SFP12', 'SFP13',
        'SFP14', 'SFP15_5', 'SFP15', 'SFP16', 'SFP17', 'SFP18', 'SFP19',
        'SFP1', 'SFP20', 'SFP21_5', 'SFP22_5', 'SFP22', 'SFP23', 'SFP24',
        'SFP2', 'SFP30_5', 'SFP31', 'SFP32', 'SFP33', 'SFP34', 'SFP39',
        'SFP40', 'SFP41', 'SFP42', 'SFP45', 'SFP46', 'SFP47', 'SFP48', 'SFP49',
        'SFP4', 'SFP50', 'SFP51', 'SFP52', 'SFP53', 'SFP54', 'SFP5_5',
        'SFP55', 'SFP56', 'SFP57_2', 'SFP57_3', 'SFP57', 'SFP5', 'SFP61',
        'SFP62', 'SFP63', 'SFP64', 'SFP6_5', 'SFP61', 'SFP62', 'SFP63',
        'SFP64', 'SFP6_5', 'SFP65', 'SFP66', 'SFP67', 'SFP69', 'SFP6', 'SFP70',
        'SFP7', 'SFP8', 'SFP9_5', 'SFP9', 'SUG', 'SLI', 'SOM', 'SR', 'UFB1',
        'UFB2', 'UFB4', 'UK', 'UK_IN', 'UK_MID', 'UK_OFF', 'WFB', 'WFS', 'WS'
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
                base_dir + '/FKdbv2_' + product + '_TS_VSNPP_daily_' + roi +
                '.csv'
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
