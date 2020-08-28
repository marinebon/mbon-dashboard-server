This document outlines how to create a new dashboard stack branching off from the master.
If you view a graph of the various branches of this repository (see the github network graph [here](https://github.com/marinebon/mbon-dashboard-server/network)) you should see that there are many `client-*` branches forking off from the "master" branch.
This document will explain how to create a new `client-*` branch for a new project.

## Initial Setup
1. set up local copy of the master branch
    1. `git clone https://github.com/marinebon/mbon-dashboard-server`
    2. `cd mbon-dashboard-server`
2. create & use your new branch
    1. `git branch client-your_branch_name_here`
    2. `git checkout client-your_branch_name_here`
3. make basic setup changes
    1. change `localhost` to your machine's ip in `docker-compose.yml`
4. commit your changes
    1. `git commit -a -m "initial client setup"`
5. push new branch to github
    1. `git push origin client-your_branch_name_here`
