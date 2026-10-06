#!/bin/bash
# ==============================================================================
# Database Backup Script for Youth Affairs Bot (PostgreSQL)
# ==============================================================================

set -e

BACKUP_DIR="/opt/youth-bot/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/youth_bot_backup_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=14

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting database backup..."

# Extract DB credentials from .env or use defaults
DB_NAME="${DB_NAME:-youth_bot}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# Perform dump and gzip compression
PGPASSWORD="${DB_PASSWORD:-password}" pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" | gzip > "${BACKUP_FILE}"

echo "[$(date)] Backup successfully saved to ${BACKUP_FILE} (Size: $(du -h "${BACKUP_FILE}" | cut -f1))"

# Clean up backups older than retention days
echo "[$(date)] Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -type f -name "youth_bot_backup_*.sql.gz" -mtime +"${RETENTION_DAYS}" -exec rm -f {} \;

echo "[$(date)] Backup process completed successfully."
