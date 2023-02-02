## Linux
Within this directory there must exist a directory `pgdata`.
This directory is used to store PostgreSQL data.
You must create this empty directory (`mkdir ./postgres/pgdata`)

Normally I would drop a `.gitignore` in the directory and set it to ignore everything in the dir (`./*`) but PostgreSQL absolutely insists that there is nothing at all in this directory on db init.

## Windows
Because of permissions issues the `./pgdata` directory cannot be used on windows hosts.
The "windows only postgres section in `docker-compose.yml` should be uncommented and a docker volume must be created manually: `docker volume create --name postgresql-volume -d local`
