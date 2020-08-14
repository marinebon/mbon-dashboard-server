Airflow is the orchestration framework which controls scheduling, running, and tracking job completion.

# workflows
## add a new DAG
To add a new DAG:

1. `crontab -e` & comment out the `git pull` line 
1. create a new python file in `mbon-dashboard-server/airflow/dags/` 

1. Navigate to the airflow gui (my-dashboard:8888/)
2. sign in in necessary
3. toggle "on" all desired dags
