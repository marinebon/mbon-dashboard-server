## Modifying dashboards
Dashboards can be edited through grafana's user interface.
Changes to dashboards will not automatically persist when the container is recreated.

Dashboards in `./grafana/provisioning/dashboards` will be added to grafana when the container is created.
You may add your own .json dashboard export files to this directory.

Similarly datasources can be added by modifying the contents of `./grafana/provisioning/datasources`.

A cronjob can be configured to export & `git commit` these dashboards nightly (TODO: + details).
