#!/bin/bash
# NOTE: this works along with a cronjob similar to the following in order to update ssl certs automatically.
#       example crontab entry:
# 0   0,12 *   *   * cd /home/murray_tylar/mbon-dashboard-server && /bin/bash ./cert_update.sh
cd /home/murray_tylar/mbon-dashboard-server

docker stop nginx

docker run --rm \
  -v ~/mbon-dashboard-server/certs:/etc/letsencrypt \
  -v ~/mbon-dashboard-server/certs:/var/lib/letsencrypt \
  -p 80:80 \
  certbot/certbot certonly \
    --standalone \
    -d mbon-dashboards.marine.usf.edu \
    --email tylarmurray@usf.edu \
    --agree-tos \
    --no-eff-email \
    --non-interactive

cp certs/live/mbon-dashboards.marine.usf.edu/*pem certs/.

docker compose up --build -d nginx
