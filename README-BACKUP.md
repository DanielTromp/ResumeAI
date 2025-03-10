# ResumeAI Backup and Restore Guide

This document provides a comprehensive guide on backing up and restoring your ResumeAI application.

## Quick Reference

```bash
# Create a backup
./manage.sh backup

# Restore from a backup
./manage.sh restore backups/resumeai_backup_20250310_123456.tar.gz
```

## Backup System Overview

The ResumeAI backup system creates comprehensive backups of:

1. **Code** - All application code (backend and frontend)
2. **Configuration** - Environment variables and Docker configurations
3. **Database** - PostgreSQL database dump
4. **Files** - Resume PDFs and other data files
5. **Docker Volumes** - Data from Docker volumes (when running in Docker mode)

Each backup is a self-contained archive that can fully restore your application to the state it was in when the backup was created.

## Creating Backups

### Standard Backup

To create a standard backup of everything:

```bash
./manage.sh backup
```

This will:
- Back up all code from backend and frontend directories
- Export database to SQL dump
- Back up configuration files (.env files)
- Back up all resume files
- Back up Docker volumes (if Docker is running)
- Create a detailed backup log

The backup will be stored in the `backups/` directory with a timestamp in the filename.

### What Gets Backed Up

The backup includes:

- **Code**
  - Backend Python code
  - Frontend React code
  - Custom scripts and utilities

- **Database**
  - Complete PostgreSQL database dump
  - Database structure (tables, indexes, functions)
  - All data (resumes, vacancies, matches)

- **Configuration**
  - Environment variables (.env files)
  - Docker Compose configuration
  - Application settings

- **Files**
  - Resume PDFs
  - Other data files

- **Docker Volumes**
  - backend_data
  - resume_storage
  - postgres_data (raw data as last resort)

## Restoring from Backups

### Standard Restore

To restore your application from a backup:

```bash
./manage.sh restore backups/resumeai_backup_20250310_123456.tar.gz
```

This will:
1. Extract the backup archive
2. Restore all code and configuration files
3. Restore the database (if Docker is running or PostgreSQL is installed locally)
4. Restore Docker volumes (if Docker is running)
5. Restore resume files and other data
6. Create a detailed restore log

### Restore Process Details

The restore process follows these steps:

1. **Preparation**
   - Checks if the backup file exists and is valid
   - Creates a temporary directory for the restoration
   - Logs all actions to a restore log file

2. **Stopping Services**
   - Stops any running Docker containers
   - Ensures clean environment for restoration

3. **Code Restoration**
   - Restores backend code
   - Restores frontend code

4. **Configuration Restoration**
   - Restores .env files and Docker configuration
   - Ensures proper settings for the application

5. **Database Restoration**
   - If Docker is running:
     - Finds the PostgreSQL container
     - Drops and recreates the database
     - Applies the SQL dump from the backup
   - If running locally with PostgreSQL installed:
     - Uses psql to restore the database directly
   - If neither is available:
     - Saves the SQL dump for manual restoration

6. **File Restoration**
   - Restores resume files
   - Restores Docker volumes (if Docker is running)

7. **Completion**
   - Cleans up temporary files
   - Provides a summary of the restoration

## Verification After Restore

After restoring, you should:

1. Start the application:
   ```bash
   ./manage.sh docker-up    # For Docker mode
   # OR
   ./manage.sh backend      # For local mode
   ```

2. Verify the backend is working:
   ```bash
   curl http://localhost:8008/
   ```

3. Check the database connectivity:
   ```bash
   docker exec -it resumeai_db psql -U postgres -d resumeai -c "SELECT COUNT(*) FROM resumes;"
   ```

4. Verify resume files are accessible:
   ```bash
   ls -la backend/app/resumes/
   # OR if using Docker
   docker exec resumeai_backend ls -la /app/app/resumes/
   ```

## Scheduled Backups

The Docker setup includes a backup service that creates backups automatically every 24 hours. You can modify the schedule in the `docker-compose.yml` file.

To manually trigger a backup from the Docker service:

```bash
docker compose exec backup /bin/sh -c 'DATE=$(date +%Y%m%d_%H%M%S); tar -czf /backups/resumeai_backup_$DATE.tar.gz /backup'
```

## Troubleshooting

### Backup Issues

If you encounter issues with backups:

- Check disk space:
  ```bash
  df -h
  ```

- Verify Docker is running (for Docker-based backups):
  ```bash
  docker ps
  ```

- Check database connection:
  ```bash
  docker exec -it resumeai_db psql -U postgres -c "\l"
  ```

### Restore Issues

If you encounter issues with restoration:

- Check the restore log for errors:
  ```bash
  cat backups/restore_log_*.txt | grep -i error
  ```

- Verify the backup file integrity:
  ```bash
  tar -tzf backups/resumeai_backup_*.tar.gz
  ```

- If database restoration fails:
  1. Start the database service:
     ```bash
     docker compose up -d db
     ```
  2. Manually restore the database:
     ```bash
     docker exec -i resumeai_db psql -U postgres -d resumeai < database_restore/resumeai.sql
     ```

## Manual Database Restoration

If the automatic database restoration fails, you can manually restore it:

### Using Docker

```bash
# Copy the SQL dump to the container
docker cp database_restore/resumeai.sql resumeai_db:/tmp/

# Drop and recreate the database
docker exec -it resumeai_db psql -U postgres -c "DROP DATABASE IF EXISTS resumeai;"
docker exec -it resumeai_db psql -U postgres -c "CREATE DATABASE resumeai;"

# Restore from the SQL dump
docker exec -it resumeai_db psql -U postgres -d resumeai -f /tmp/resumeai.sql
```

### Using psql directly

```bash
# Set environment variables
export PGHOST=localhost
export PGPORT=5432
export PGUSER=postgres
export PGPASSWORD=postgres

# Drop and recreate the database
psql -c "DROP DATABASE IF EXISTS resumeai;"
psql -c "CREATE DATABASE resumeai;"

# Restore from the SQL dump
psql -d resumeai -f database_restore/resumeai.sql
```

### Using pgAdmin

1. Open pgAdmin (http://localhost:8080 if using Docker)
2. Log in with credentials (admin@resumeai.com / admin)
3. Connect to the database server
4. Right-click on "Databases" and select "Create" > "Database..."
5. Name it "resumeai" and click "Save"
6. Right-click on the new database and select "Restore..."
7. Browse to select the SQL dump file
8. Click "Restore" to start the restoration

## Best Practices

- Create regular backups, especially before major changes
- Store backups in multiple locations (cloud storage, external drives)
- Test restores periodically to ensure backups are valid
- Keep backup logs for troubleshooting
- Make sure all Docker containers are running before creating a backup
- Stop the application before restoring (to avoid conflicts)