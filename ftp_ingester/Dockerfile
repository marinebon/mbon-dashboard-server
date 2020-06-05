# This docker image sets up an FTP server which will
# 1. Allow anon downloads of files within the `/home/vsftpd/public` volume.
# 2. Accept uploads of FWC .csv coral disease data files into `/home/vsftpd/uploads`.
#    These uploads are automatically ingested into InfluxDB.
FROM fauria/vsftpd

# overwrite the vstfpd default from upstream
COPY vsftpd.conf /etc/vsftpd/

# TODO:
# * set up users & passwords
# * use /etc/vsftpd_user_conf/$USERNAME to config an upload user.
#   ref: https://www.gotothings.com/linux/vsftpd-upload-only-for-that-user
#   and/or use bind mounts to limit uploads to one folder
#   ref: https://serverfault.com/a/556129/392592
