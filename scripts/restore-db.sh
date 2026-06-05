#!/usr/bin/env bash
# ── VeinConnect AI — Database Restore Script ─────────────────────────────────
# Destructive script to restore a snapshot into the running database container.
# Warning: Overwrites existing records in the database container.

# Fail script on any error
set -eo pipefail

# Configuration
CONTAINER_NAME="veinconnect_db"
DB_USER="veinconnect"
DB_NAME="veinconnect_db"

# Help manual
show_help() {
    echo "Usage: $0 [path-to-backup-file.sql.gz]"
    echo "Example: $0 ./backups/veinconnect_backup_2026-06-03_212000.sql.gz"
}

# Check input arguments
if [ -z "$1" ]; then
    echo "ERROR: Missing backup file argument." >&2
    show_help
    exit 1
fi

BACKUP_FILE="$1"

# Verify backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file does not exist at: ${BACKUP_FILE}" >&2
    exit 1
fi

# Ensure running inside running docker container
if [ "$(docker inspect -f '{{.State.Running}}' "${CONTAINER_NAME}" 2>/dev/null)" != "true" ]; then
    echo "ERROR: Database container '${CONTAINER_NAME}' is not running." >&2
    exit 1
fi

# Destructive warning confirmation
echo "⚠️ WARNING: You are about to overwrite the database '${DB_NAME}' with data from:"
echo "   ${BACKUP_FILE}"
echo "   This will destroy all current database contents!"
read -p "Are you absolutely sure you want to proceed? (y/N): " CONFIRMATION

if [[ ! "${CONFIRMATION}" =~ ^[Yy]$ ]]; then
    echo "Restoration aborted by user."
    exit 0
fi

echo "=== Starting database restoration ==="

# Decompress and load dump file
echo "Loading schema and restoring data..."
gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}"

echo "Database successfully restored from snapshot!"
echo "=== Restoration Process Complete ==="
