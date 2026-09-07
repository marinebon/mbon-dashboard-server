# Cheatsheet

## Shell into the server

The stack runs on a Google Cloud Platform VM (see `documentation/hosting_details.md`).
SSH in via the GCP console ("SSH" button on the instance) or `gcloud compute ssh`,
then:

```bash
cd ~/mbon-dashboard-server
```

## Inspect container logs

```bash
# tail logs from all containers
docker compose logs -f

# one service
docker compose logs -f grafana

# inspect a container
docker inspect nginx
```

## Common operations

```bash
docker compose ps                 # what's running
docker compose up -d              # (re)start the stack
docker compose restart grafana    # restart one service
docker exec nginx nginx -s reload # reload nginx config / certs, no downtime
```
