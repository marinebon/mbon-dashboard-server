## load data from csv
TODO: https://www.influxdata.com/blog/how-to-write-points-from-csv-to-influxdb/
and https://www.influxdata.com/blog/how-to-setup-influxdb-telegraf-and-grafana-on-docker-part-1/


### Test http interface
Navigate to `localhost:5000/query?q=SHOW DATABASES` and enter credentials.


test with curl:
```bash
curl -G http://localhost:8086/query --data-urlencode "q=SHOW DATABASES" -u "influx_user:influx_user_pw"
```
