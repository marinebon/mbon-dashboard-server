# Dashboard Editing Workflow
This outlines how to edit grafana dashboards within this framework.

## use grafana GUI & GitHub GUI
To do this you must have:
1. a username and password to log into your grafana server
2. a github account
3. editor priveledges on this (`/marinebon/mbon-dashboard-server`) github repository
    * if you are unsure please [open an issue so we can help](https://github.com/marinebon/mbon-dashboard-server/issues).

### making a change
1. sign in to your grafana server
2. navigate to the dashboard & panel you wish to edit, click the edit icon
3. make your changes
4. click the save icon (top right)
5. copy the JSON
6. navigate to your `client-*` branch (topish left dropdown box that says "master")
7. navigate to the relevant dashboard json file on github
    * it will be in `/grafana/provisioning/dashboards` on your branch
8. click the edit icon
9. select all, delete, & paste in your new JSON
10. scroll down, enter commit message (description of your changes), and click commit button

Your changes are now forever saved and can be used by our grafana servers.
There are a few more steps to get the changes onto the server.

### pulling changes from github to your server
1. ssh into your server
2. navigate to `~/mbon-dashboard-server` (or wherever you keep this repo)
3. `git pull`

Changes from the github remote should now be on your server repo and dashboard edits will show up immediately.
No service restarting or similar is needed.
