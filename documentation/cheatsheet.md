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

## Transferring files to the server

The VM lives on GCP. Use `gcloud compute scp` from your **laptop** to copy files up
(no need to know the IP address):

```bash
# single file → server home dir
gcloud compute scp /path/to/local/file.pem murray_tylar@<INSTANCE_NAME>:~/

# whole directory
gcloud compute scp --recurse /path/to/local/dir/ murray_tylar@<INSTANCE_NAME>:~/

# copy straight into the cert staging area (must already exist on the server)
gcloud compute scp fullchain.pem privkey.pem \
    murray_tylar@<INSTANCE_NAME>:~/mbon-dashboard-server/certs/incoming/
```

`<INSTANCE_NAME>` is visible in the GCP console VM list (e.g. `mbon-dashboard-server`).
Add `--zone <ZONE>` if prompted (e.g. `--zone us-east1-b`).

If you prefer plain `scp` (you'll need the external IP from the GCP console):

```bash
scp /path/to/file.pem murray_tylar@<EXTERNAL_IP>:~/
```

> **Cert workflow**: after uploading, follow the install steps in
> `documentation/hosting_details.md` → "When USF IT delivers a new cert".
> Also see `certs/README.md` for a quick-reference version.

## Common operations

```bash
docker compose ps                 # what's running
docker compose up -d              # (re)start the stack
docker compose restart grafana    # restart one service
docker exec nginx nginx -s reload # reload nginx config / certs, no downtime
```
