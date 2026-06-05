#!/usr/bin/env bash
# ── VeinConnect AI — Database Backup Script ──────────────────────────────────
# Intended for Cron scheduling or manual administrative snapshotting.
# Operates by executing pg_dump inside the active database container.

# Fail script on any error
set -eo pipefail

# Configuration
CONTAINER_NAME="veinconnect_db"
DB_USER="veinconnect"
DB_NAME="veinconnect_db"
BACKUP_DIR="./backups"
RETENTION_DAYS=7
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/veinconnect_backup_${TIMESTAMP}.sql.gz"

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

echo "=== Starting database backup for ${DB_NAME} ==="

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker CLI is not installed or not in PATH." >&2
    exit 1
fi

# Check if the container is running
if [ "$(docker inspect -f '{{.State.Running}}' "${CONTAINER_NAME}" 2>/dev/null)" != "true" ]; then
    echo "ERROR: Database container '${CONTAINER_NAME}' is not running." >&2
    exit 1
fi

# Run pg_dump and compress
echo "Dumping database schema and data..."
docker exec -t "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" | gzip > "${BACKUP_FILE}"

# Validate backup file size
if [ ! -s "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file was created but is empty." >&2
    rm -f "${BACKUP_FILE}"
    exit 1
fi

echo "Backup successfully written to: ${BACKUP_FILE}"
echo "Backup size: $(du -sh "${BACKUP_FILE}" | cut -f1)"

# Prune old backups (older than RETENTION_DAYS)
echo "Pruning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -type f -name "veinconnect_backup_*.sql.gz" -mtime +"${RETENTION_DAYS}" -exec rm -f {} \; -print || true

echo "=== Backup Process Complete ==="
