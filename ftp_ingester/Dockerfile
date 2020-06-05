# This docker image sets up an FTP server which will
# 1. Allow downloads of files within the `/home/vsftpd/public` volume.
# 2. Accept uploads of FWC .csv coral disease data files into `/home/vsftpd/uploads`.
#    These uploads are automatically ingested into InfluxDB.
FROM fauria/vsftpd

# overwrite the vstfpd default from upstream
COPY vsftpd.conf /etc/vsftpd/
