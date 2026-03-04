Airflow is the orchestration framework which controls scheduling, running, and tracking job completion.

# workflows
## Hard reset a DAG
```
DAG_ID='ingest_comps_buoys'
docker exec -it mbon-dashboard-server-airflow-scheduler-1 airflow dags pause $DAG_ID
docker exec -it mbon-dashboard-server-airflow-scheduler-1 airflow dags delete -y $DAG_ID
docker exec -it mbon-dashboard-server-airflow-scheduler-1 airflow dags unpause $DAG_ID
```
