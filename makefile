.PHONY: rebuild backup-influxdb restore-influxdb

rebuild:
	docker compose down --rmi all -v && docker compose build --no-cache && docker compose up -d

# Back up the InfluxDB data volume to ./backups/influxdb/<timestamp>/
# Usage: make backup-influxdb
BACKUP_DIR := backups/influxdb/$(shell date -u +%Y%m%dT%H%M%SZ)
backup-influxdb:
	mkdir -p $(BACKUP_DIR)
	docker exec influxdb sh -c 'influx backup --host http://localhost:8086 --token "$$DOCKER_INFLUXDB_INIT_ADMIN_TOKEN" /tmp/influx-backup'
	docker cp influxdb:/tmp/influx-backup/. $(BACKUP_DIR)
	docker exec influxdb rm -rf /tmp/influx-backup
	@echo "Backup written to $(BACKUP_DIR)"

# Restore the InfluxDB data volume from a backup directory.
# Usage: make restore-influxdb BACKUP_PATH=backups/influxdb/<timestamp>
BACKUP_PATH ?=
restore-influxdb:
	@if [ -z "$(BACKUP_PATH)" ]; then \
		echo "ERROR: BACKUP_PATH is required. Usage: make restore-influxdb BACKUP_PATH=backups/influxdb/<timestamp>"; \
		exit 1; \
	fi
	docker cp $(BACKUP_PATH)/. influxdb:/tmp/influx-restore
	docker exec influxdb sh -c 'influx restore --host http://localhost:8086 --token "$$DOCKER_INFLUXDB_INIT_ADMIN_TOKEN" --full /tmp/influx-restore'
	docker exec influxdb rm -rf /tmp/influx-restore
	@echo "Restore complete from $(BACKUP_PATH)"
