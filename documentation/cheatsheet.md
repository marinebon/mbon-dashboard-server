


## Shell into server

1. Connect to UCSB VPN via Secure Pulse
1. SSH, eg for Ben:
    ```bash
    pass=`cat ~/private/bbest@mbon.marine.usf.edu`
    sshpass -p $pass ssh bbest@mbon.marine.usf.edu
    ```




### Inspect docker logs

To tail the logs from the Docker containers in realtime, run:

```bash
docker-compose logs -f

docker inspect rstudio-shiny
```
