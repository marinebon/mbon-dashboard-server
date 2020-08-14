## Modifying dashboards
Dashboards can be edited through grafana's user interface.
Changes to dashboards will not automatically persist when the container is recreated.

Dashboards in `./grafana/provisioning/dashboards` will be added to grafana when the container is created.
You may add your own .json dashboard export files to this directory.

Similarly datasources can be added by modifying the contents of `./grafana/provisioning/datasources`.

### Dashboard editing workflow
0. sign in (bottom left button)
1. modify the dashboard
2. click "save"
    - a message should pop up "Cannot save provisioned dashboard"
    - if the message does not pop up go to settings -> JSON model
3. copy all of the json data
4. go to [mbon-dashboard-server/grafana/provisioning/dashboards/](https://github.com/marinebon/mbon-dashboard-server/tree/master/grafana/provisioning/dashboards)
5. select the git branch of your dashboard (top right, default is "master")
    - your branch is probably called something like client-fwc, client-fknms, or client-fgbnms
6. click on the dashboard definition you wish to edit
7. edit the file (pencil button, top right)
8. delete all of the content and replace it with the json you copied from grafana
9. at the bottom of the page descibe your change under "commit changes"
10. click "commit changes" (bottom left)
11. Your changes should be live on the site within an hour.



## Post-install manual configuration:

1. under configuration > preferences
    1. set org name
    2. set Home Dashboard to "Home Dashboard"


## Troubleshooting

Sometimes when restarting grafana there is some confusion about the permissions for the grafana-storage directory.
As a workaround:
    1. `docker container stop grafana`
    2. `chmod -R 777 grafana/grafana-storage`
    3. `docker container start grafana`
