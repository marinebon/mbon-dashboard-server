# erddap-config
ERDDAP config files (setup.xml, datasets.xml)


## Modifying for your datasets
1. create symlinks in `erddap/erddap_datasets` pointing to your data directories.
    * `ln -s /srv/imars-objects/fk/MEAN_7D_VSNPP/OC erddap/erddap_datasets/.`
2. modify `erddap/datasets.xml` to describe your datasets.
