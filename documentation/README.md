# Documentation index

Project overview and quickstart are in the repo-root [`README.md`](../README.md).

| Doc | What it covers |
| --- | --- |
| [`hosting_details.md`](hosting_details.md) | The GCP host; how nginx consumes the TLS cert; the Let's Encrypt → eMSign migration and the manual cert-install procedure. |
| [`server_setup.md`](server_setup.md) | Standing up the full stack on a fresh machine, plus the cron jobs. |
| [`cheatsheet.md`](cheatsheet.md) | Everyday shell / `docker compose` commands on the server. |
| [`dashboard_editing_workflow.md`](dashboard_editing_workflow.md) | Editing Grafana dashboards via the Grafana GUI + GitHub, then pulling to the server. |
| [`csv_into_dashboard.md`](csv_into_dashboard.md) | How CSV data is made available over HTTP and ingested by Airflow. |
| `Untitled Diagram.drawio` | Early architecture sketch (2020). Not maintained. |
| [`archive/`](archive/) | Deprecated docs kept for history (per-client-branch deployment model). |

Container-specific notes live next to each service:
[`../grafana/README.md`](../grafana/README.md),
[`../influxdb/README.md`](../influxdb/README.md),
[`../postgres/README.md`](../postgres/README.md),
[`../airflow/README.md`](../airflow/README.md).
