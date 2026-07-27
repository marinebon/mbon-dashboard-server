.PHONY: rebuild backup-influxdb restore-influxdb

rebuild:
	docker compose down --rmi all -v && docker compose build --no-cache && docker compose up -d

# Docker Compose project name → volume prefix (override if your project name differs)
COMPOSE_PROJECT ?= mbon-dashboard-server
INFLUX_VOLUME   := $(COMPOSE_PROJECT)_influx-data-volume

# ---------------------------------------------------------------------------
# backup-influxdb
#   Stops influxdb, tars the raw volume into backups/influxdb/<timestamp>/,
#   then restarts it. Uses a temporary Alpine container so no influx CLI
#   HTTP calls are involved — completely reliable.
#   Usage: make backup-influxdb
# ---------------------------------------------------------------------------
BACKUP_DIR := backups/influxdb/$(shell date -u +%Y%m%dT%H%M%SZ)
backup-influxdb:
	mkdir -p $(BACKUP_DIR)
	docker compose stop influxdb
	docker run --rm \
		-v $(INFLUX_VOLUME):/data:ro \
		-v $(PWD)/$(BACKUP_DIR):/backup \
		alpine tar -czf /backup/influxdb-data.tar.gz -C /data .
	docker compose start influxdb
	@echo "Backup written to $(BACKUP_DIR)/influxdb-data.tar.gz"

# ---------------------------------------------------------------------------
# restore-influxdb
#   Stops influxdb, wipes the volume, extracts the backup tar, then
#   restarts influxdb. Defaults to the most recent backup found under
#   backups/influxdb/; override with BACKUP_PATH=backups/influxdb/<timestamp>
#   Usage: make restore-influxdb [BACKUP_PATH=backups/influxdb/<timestamp>]
# ---------------------------------------------------------------------------
BACKUP_PATH ?= $(shell ls -dt backups/influxdb/*/ 2>/dev/null | head -1 | sed 's|/$$||')
restore-influxdb:
	@if [ -z "$(BACKUP_PATH)" ]; then \
		echo "ERROR: No backups found. Run 'make backup-influxdb' first."; \
		exit 1; \
	fi
	@if [ ! -f "$(BACKUP_PATH)/influxdb-data.tar.gz" ]; then \
		echo "ERROR: $(BACKUP_PATH)/influxdb-data.tar.gz not found."; \
		exit 1; \
	fi
	@echo "Restoring from $(BACKUP_PATH)/influxdb-data.tar.gz ..."
	docker compose stop influxdb
	docker run --rm \
		-v $(INFLUX_VOLUME):/data \
		-v $(PWD)/$(BACKUP_PATH):/backup:ro \
		alpine sh -c "find /data -mindepth 1 -delete && tar -xzf /backup/influxdb-data.tar.gz -C /data"
	docker compose start influxdb
	@echo "Restore complete. influxdb restarted."
