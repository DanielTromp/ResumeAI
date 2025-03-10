#!/bin/bash
# ResumeAI Management Script
# This script provides a unified interface for managing ResumeAI development and deployment

# Function to display help information
show_help() {
    echo "ResumeAI Management Script"
    echo ""
    echo "Usage: ./manage.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  backend        Start/restart the backend service"
    echo "  frontend       Start/restart the frontend service"
    echo "  check          Check the status of running services"
    echo "  backup         Create a backup of the application"
    echo "  restore        Restore from a backup"
    echo "  init-db        Initialize the PostgreSQL database"
    echo "  setup          Setup the application (activate venv, install dependencies)"
    echo "  config         Show or generate configuration information"
    echo "  docker-up      Start Docker-based services"
    echo "  docker-down    Stop Docker-based services"
    echo "  help           Show this help message"
    echo ""
    echo "Options:"
    echo "  --docker       Run the command in Docker environment"
    echo "  --local        Run the command in local environment (default)"
    echo ""
    echo "Examples:"
    echo "  ./manage.sh backend      # Start the backend service locally"
    echo "  ./manage.sh frontend     # Start the frontend service locally"
    echo "  ./manage.sh backup       # Create a backup"
    echo "  ./manage.sh restore backups/my_backup.tar.gz  # Restore from backup"
    echo "  ./manage.sh docker-up    # Start all Docker services"
    echo "  ./manage.sh config       # Show current configuration"
    echo "  ./manage.sh config --template  # Generate a template .env file"
    echo "  ./manage.sh config --section database  # Show database configuration"
    echo ""
}

# Function to activate the virtual environment
activate_venv() {
    # Activate virtual environment if available
    if [ -d "venv" ]; then
        echo "Activating virtual environment..."
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        elif [ -f "venv/Scripts/activate" ]; then
            source venv/Scripts/activate
        fi
    elif [ -d ".venv" ]; then
        echo "Activating virtual environment..."
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
        elif [ -f ".venv/Scripts/activate" ]; then
            source .venv/Scripts/activate
        fi
    else
        echo "No virtual environment found. Consider creating one with: python -m venv venv"
    fi
}

# Function to start/restart the backend
start_backend() {
    echo "Starting backend service..."

    # Stop any existing backend processes
    pkill -f "uvicorn main:app" || true
    sleep 2

    # Activate the virtual environment
    activate_venv

    # Make sure required packages are installed
    pip install -r requirements.txt

    # Start the backend server
    echo "Starting backend server..."
    cd backend
    python -m uvicorn main:app --host 0.0.0.0 --port 8008 --reload
}

# Function to start/restart the frontend
start_frontend() {
    echo "Starting frontend service..."

    # Stop any existing frontend processes
    pkill -f "react-scripts start" || true
    sleep 2

    # Change to frontend directory
    cd frontend

    # Install required packages
    npm install

    # Update proxy if requested
    if [ "$1" == "docker" ]; then
        sed -i '' 's/"proxy": "http:\/\/localhost:8000"/"proxy": "http:\/\/localhost:8008"/' package.json
        echo "Updated proxy to point to Docker backend at http://localhost:8008"
    fi

    # Start the frontend server
    echo "Starting frontend server..."
    npm start
}

# Function to check running services
check_services() {
    echo "Checking backend API..."
    curl -s http://localhost:8008/ | grep -o "ResumeAI" || echo "Backend not responding"

    echo "Checking frontend service..."
    curl -s http://localhost:3000 | head -5 || echo "Frontend not responding"

    if command -v docker &> /dev/null; then
        echo "Docker containers status:"
        docker ps | grep resumeai

        if [ "$(docker ps | grep resumeai)" ]; then
            echo "Network inspection:"
            docker network inspect resumeai_default | grep -A 10 "Containers" || echo "Network resumeai_default not found"
        fi
    else
        echo "Docker not installed or not running."
    fi
}

# Function to create a comprehensive backup
create_backup() {
    echo "📦 Creating comprehensive backup..."

    # Configuration
    BACKUP_DIR="./backups"
    DATE=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/resumeai_backup_$DATE.tar.gz"
    BACKUP_LOG="$BACKUP_DIR/backup_log_$DATE.txt"

    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    # Start backup log
    echo "ResumeAI Backup Log - $(date)" > "$BACKUP_LOG"
    echo "===============================" >> "$BACKUP_LOG"
    
    # Check if we're running in Docker
    DOCKER_RUNNING=false
    if [ "$(docker ps | grep resumeai)" ]; then
        DOCKER_RUNNING=true
        echo "✅ Docker is running, will include PostgreSQL database dump" | tee -a "$BACKUP_LOG"
    else
        echo "⚠️ Docker is not running, attempting alternative backup methods" | tee -a "$BACKUP_LOG"
    fi

    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    echo "📂 Created temporary directory: $TEMP_DIR" >> "$BACKUP_LOG"
    
    # Create directory structure in temp folder
    mkdir -p "$TEMP_DIR/backend"
    mkdir -p "$TEMP_DIR/frontend"
    mkdir -p "$TEMP_DIR/volumes/postgres_data"
    mkdir -p "$TEMP_DIR/volumes/backend_data" 
    mkdir -p "$TEMP_DIR/volumes/resume_storage"
    mkdir -p "$TEMP_DIR/volumes/pgadmin_data"
    mkdir -p "$TEMP_DIR/database_dump"
    mkdir -p "$TEMP_DIR/config"
    
    # Copy code directories
    echo "📂 Copying code directories..." | tee -a "$BACKUP_LOG"
    if [ -d "./backend" ]; then
        cp -r ./backend/* "$TEMP_DIR/backend/"
        echo "✅ Backend code copied" >> "$BACKUP_LOG"
    else
        echo "⚠️ Backend directory not found" >> "$BACKUP_LOG"
    fi
    
    if [ -d "./frontend" ]; then
        cp -r ./frontend/* "$TEMP_DIR/frontend/"
        echo "✅ Frontend code copied" >> "$BACKUP_LOG"
    else
        echo "⚠️ Frontend directory not found" >> "$BACKUP_LOG"
    fi
    
    # Copy configuration files
    echo "📂 Copying configuration files..." | tee -a "$BACKUP_LOG"
    if [ -f ".env" ]; then
        cp .env "$TEMP_DIR/config/"
        echo "✅ Root .env file copied" >> "$BACKUP_LOG"
    fi
    
    if [ -f "./backend/.env" ]; then
        cp ./backend/.env "$TEMP_DIR/config/backend.env"
        echo "✅ Backend .env file copied" >> "$BACKUP_LOG"
    fi
    
    if [ -f "./backend/.env.docker" ]; then
        cp ./backend/.env.docker "$TEMP_DIR/config/backend.env.docker"
        echo "✅ Backend .env.docker file copied" >> "$BACKUP_LOG"
    fi
    
    # Copy docker-compose.yml
    if [ -f "docker-compose.yml" ]; then
        cp docker-compose.yml "$TEMP_DIR/config/"
        echo "✅ docker-compose.yml copied" >> "$BACKUP_LOG"
    fi
    
    # Backup PostgreSQL database (if Docker is running)
    if [ "$DOCKER_RUNNING" = true ]; then
        echo "🔄 Backing up PostgreSQL database..." | tee -a "$BACKUP_LOG"
        
        # Check if database container is running
        if [ "$(docker ps | grep resumeai_db)" ]; then
            container_name=$(docker ps | grep resumeai_db | awk '{print $NF}')
        else
            container_name=$(docker ps | grep '_db' | head -1 | awk '{print $NF}')
        fi
        
        if [ -n "$container_name" ]; then
            echo "📦 Found database container: $container_name" >> "$BACKUP_LOG"
            
            # Create a database dump
            echo "📦 Creating database dump..." | tee -a "$BACKUP_LOG"
            docker exec $container_name pg_dump -U postgres -d resumeai > "$TEMP_DIR/database_dump/resumeai.sql"
            
            if [ $? -eq 0 ]; then
                echo "✅ Database dump created successfully" >> "$BACKUP_LOG"
            else
                echo "⚠️ Database dump failed" >> "$BACKUP_LOG"
            fi
            
            # Also export Docker volumes
            echo "📦 Exporting Docker volumes..." | tee -a "$BACKUP_LOG"
            
            # Export backend_data volume
            if [ "$(docker volume ls | grep resumeai_backend_data)" ]; then
                docker run --rm -v resumeai_backend_data:/data -v "$TEMP_DIR/volumes/backend_data:/backup" alpine tar -cf /backup/data.tar -C /data .
                echo "✅ backend_data volume exported" >> "$BACKUP_LOG"
            else
                echo "⚠️ backend_data volume not found" >> "$BACKUP_LOG"
            fi
            
            # Export resume_storage volume
            if [ "$(docker volume ls | grep resumeai_resume_storage)" ]; then
                docker run --rm -v resumeai_resume_storage:/data -v "$TEMP_DIR/volumes/resume_storage:/backup" alpine tar -cf /backup/data.tar -C /data .
                echo "✅ resume_storage volume exported" >> "$BACKUP_LOG"
            else
                echo "⚠️ resume_storage volume not found" >> "$BACKUP_LOG"
            fi
            
            # Export postgres_data volume (this is risky as it's the live database, but we include it as a last resort)
            if [ "$(docker volume ls | grep resumeai_postgres_data)" ]; then
                echo "⚠️ Exporting postgres_data volume (raw data backup)" >> "$BACKUP_LOG"
                docker run --rm -v resumeai_postgres_data:/data -v "$TEMP_DIR/volumes/postgres_data:/backup" alpine tar -cf /backup/data.tar -C /data .
                echo "✅ postgres_data volume exported (for disaster recovery only)" >> "$BACKUP_LOG"
            fi
        else
            echo "⚠️ Could not find database container" >> "$BACKUP_LOG"
        fi
    else
        echo "⚠️ Docker not running, skipping database dump" >> "$BACKUP_LOG"
        
        # Check if we can use pg_dump directly
        if command -v pg_dump &> /dev/null; then
            echo "🔄 Attempting direct PostgreSQL dump..." | tee -a "$BACKUP_LOG"
            
            # Try to use environment variables if set
            PG_HOST=${PG_HOST:-localhost}
            PG_PORT=${PG_PORT:-5432}
            PG_USER=${PG_USER:-postgres}
            PG_PASSWORD=${PG_PASSWORD:-postgres}
            PG_DATABASE=${PG_DATABASE:-resumeai}
            
            # Export password for pg_dump
            export PGPASSWORD="$PG_PASSWORD"
            
            # Try to dump the database
            pg_dump -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DATABASE" > "$TEMP_DIR/database_dump/resumeai.sql" 2>> "$BACKUP_LOG"
            
            if [ $? -eq 0 ]; then
                echo "✅ Direct database dump created successfully" >> "$BACKUP_LOG"
            else
                echo "⚠️ Direct database dump failed" >> "$BACKUP_LOG"
            fi
            
            # Unset password
            unset PGPASSWORD
        fi
    fi
    
    # Copy resumes directory (if it exists outside Docker)
    if [ -d "./app/resumes" ]; then
        echo "📂 Copying resumes directory..." | tee -a "$BACKUP_LOG"
        cp -r ./app/resumes/* "$TEMP_DIR/volumes/resume_storage/"
        echo "✅ Resumes copied" >> "$BACKUP_LOG"
    elif [ -d "./backend/app/resumes" ]; then
        echo "📂 Copying resumes directory..." | tee -a "$BACKUP_LOG"
        cp -r ./backend/app/resumes/* "$TEMP_DIR/volumes/resume_storage/"
        echo "✅ Resumes copied" >> "$BACKUP_LOG"
    fi
    
    # Save backup metadata
    echo "📝 Saving backup metadata..." | tee -a "$BACKUP_LOG"
    {
        echo "Backup created: $(date)"
        echo "ResumeAI version: $(grep -o 'Version: [0-9.]*' ./backend/app/combined_process.py | head -1 || echo 'Unknown')"
        echo "System: $(uname -a)"
        echo ""
        echo "Directory structure:"
        find "$TEMP_DIR" -type d | sort
        echo ""
        echo "Docker status:"
        docker ps 2>/dev/null || echo "Docker not running"
        echo ""
        echo "Docker volumes:"
        docker volume ls 2>/dev/null || echo "Docker not running"
    } > "$TEMP_DIR/backup_metadata.txt"
    
    # Create backup archive
    echo "📦 Creating backup archive..." | tee -a "$BACKUP_LOG"
    tar -czf "$BACKUP_FILE" -C "$TEMP_DIR" .
    
    # Clean up temporary directory
    rm -rf "$TEMP_DIR"
    
    echo "✅ Backup created: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))" | tee -a "$BACKUP_LOG"
    echo "📝 Backup log: $BACKUP_LOG"
    
    echo "
📦 Backup Summary:
- Backup file: $BACKUP_FILE
- Log file: $BACKUP_LOG
- Size: $(du -h "$BACKUP_FILE" | cut -f1)
- Date: $(date)

You can restore this backup with:
  ./manage.sh restore $BACKUP_FILE
    "
}

# Function to restore from a backup
restore_backup() {
    if [ -z "$1" ]; then
        echo "Error: No backup file specified"
        echo "Usage: ./manage.sh restore <backup_file.tar.gz>"
        exit 1
    fi

    BACKUP_FILE="$1"
    RESTORE_LOG="./backups/restore_log_$(date +%Y%m%d_%H%M%S).txt"

    # Check if backup file exists
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "❌ Error: Backup file $BACKUP_FILE not found"
        exit 1
    fi

    echo "🔄 Restoring from backup: $BACKUP_FILE" | tee -a "$RESTORE_LOG"
    echo "📝 Restore log: $RESTORE_LOG"
    echo "===============================" >> "$RESTORE_LOG"
    echo "Restore started: $(date)" >> "$RESTORE_LOG"
    echo "Backup file: $BACKUP_FILE" >> "$RESTORE_LOG"
    echo "===============================" >> "$RESTORE_LOG"

    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    echo "📂 Created temporary directory: $TEMP_DIR" >> "$RESTORE_LOG"

    # Extract backup archive
    echo "📦 Extracting backup archive..." | tee -a "$RESTORE_LOG"
    tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"
    
    # Check if extraction was successful
    if [ $? -ne 0 ]; then
        echo "❌ Failed to extract backup archive. The file may be corrupt." | tee -a "$RESTORE_LOG"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    # Display backup metadata if available
    if [ -f "$TEMP_DIR/backup_metadata.txt" ]; then
        echo "📋 Backup metadata:" | tee -a "$RESTORE_LOG"
        cat "$TEMP_DIR/backup_metadata.txt" | tee -a "$RESTORE_LOG"
    fi

    # Check what's in the backup
    echo "📋 Backup contains:" | tee -a "$RESTORE_LOG"
    find "$TEMP_DIR" -type d -maxdepth 2 | sort >> "$RESTORE_LOG"
    
    # Check if this is a valid backup
    if [ ! -d "$TEMP_DIR/backend" ] && [ ! -d "$TEMP_DIR/database_dump" ]; then
        echo "❌ This does not appear to be a valid ResumeAI backup (missing essential components)." | tee -a "$RESTORE_LOG"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Restore cancelled" | tee -a "$RESTORE_LOG"
            rm -rf "$TEMP_DIR"
            exit 1
        fi
    fi

    # Check if current installation exists and confirm overwrite
    if [ -d "./backend" ] || [ -d "./frontend" ]; then
        echo "⚠️ This will overwrite your current installation." | tee -a "$RESTORE_LOG"
        read -p "Continue? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Restore cancelled" | tee -a "$RESTORE_LOG"
            rm -rf "$TEMP_DIR"
            exit 1
        fi
    fi

    # Stop running services if they exist
    if [ "$(docker ps | grep resumeai)" ]; then
        echo "🛑 Stopping running containers..." | tee -a "$RESTORE_LOG"
        docker compose down
        echo "✅ Containers stopped" >> "$RESTORE_LOG"
    fi

    # Create necessary directories if they don't exist
    mkdir -p backend
    mkdir -p frontend
    
    # Restore code directories
    echo "🔄 Restoring code directories..." | tee -a "$RESTORE_LOG"
    if [ -d "$TEMP_DIR/backend" ]; then
        echo "🔄 Restoring backend code..." | tee -a "$RESTORE_LOG"
        cp -r "$TEMP_DIR/backend/"* ./backend/
        echo "✅ Backend code restored" >> "$RESTORE_LOG"
    else
        echo "⚠️ No backend code found in backup" | tee -a "$RESTORE_LOG"
    fi

    if [ -d "$TEMP_DIR/frontend" ]; then
        echo "🔄 Restoring frontend code..." | tee -a "$RESTORE_LOG"
        cp -r "$TEMP_DIR/frontend/"* ./frontend/
        echo "✅ Frontend code restored" >> "$RESTORE_LOG"
    else
        echo "⚠️ No frontend code found in backup" | tee -a "$RESTORE_LOG"
    fi

    # Restore configuration files
    echo "🔄 Restoring configuration files..." | tee -a "$RESTORE_LOG"
    
    if [ -f "$TEMP_DIR/config/.env" ]; then
        cp "$TEMP_DIR/config/.env" ./.env
        echo "✅ Root .env file restored" >> "$RESTORE_LOG"
    fi
    
    if [ -f "$TEMP_DIR/config/backend.env" ]; then
        cp "$TEMP_DIR/config/backend.env" ./backend/.env
        echo "✅ Backend .env file restored" >> "$RESTORE_LOG"
    fi
    
    if [ -f "$TEMP_DIR/config/backend.env.docker" ]; then
        cp "$TEMP_DIR/config/backend.env.docker" ./backend/.env.docker
        echo "✅ Backend .env.docker file restored" >> "$RESTORE_LOG"
    fi
    
    if [ -f "$TEMP_DIR/config/docker-compose.yml" ]; then
        cp "$TEMP_DIR/config/docker-compose.yml" ./docker-compose.yml
        echo "✅ docker-compose.yml restored" >> "$RESTORE_LOG"
    fi

    # Restore Docker volumes
    if [ -d "$TEMP_DIR/volumes" ]; then
        echo "🔄 Restoring Docker volumes..." | tee -a "$RESTORE_LOG"
        
        # First check if Docker is available
        if command -v docker &> /dev/null; then
            # Create volumes if they don't exist
            echo "🔄 Creating Docker volumes if they don't exist..." >> "$RESTORE_LOG"
            docker volume create resumeai_backend_data
            docker volume create resumeai_resume_storage
            docker volume create resumeai_postgres_data
            docker volume create resumeai_pgadmin_data
            
            # Restore volume data
            if [ -f "$TEMP_DIR/volumes/backend_data/data.tar" ]; then
                echo "🔄 Restoring backend_data volume..." | tee -a "$RESTORE_LOG"
                docker run --rm -v resumeai_backend_data:/data -v "$TEMP_DIR/volumes/backend_data:/backup" alpine /bin/sh -c "cd /data && tar -xf /backup/data.tar"
                echo "✅ backend_data volume restored" >> "$RESTORE_LOG"
            else
                echo "⚠️ No backend_data volume backup found" >> "$RESTORE_LOG"
            fi
            
            if [ -f "$TEMP_DIR/volumes/resume_storage/data.tar" ]; then
                echo "🔄 Restoring resume_storage volume..." | tee -a "$RESTORE_LOG"
                docker run --rm -v resumeai_resume_storage:/data -v "$TEMP_DIR/volumes/resume_storage:/backup" alpine /bin/sh -c "cd /data && tar -xf /backup/data.tar"
                echo "✅ resume_storage volume restored" >> "$RESTORE_LOG"
            else
                echo "⚠️ No resume_storage volume backup found" >> "$RESTORE_LOG"
            fi
            
            # Normally we would not restore the postgres_data volume directly, as this can cause issues
            # Instead, we'll use the SQL dump to restore the database
        else
            echo "⚠️ Docker not available, can't restore Docker volumes" | tee -a "$RESTORE_LOG"
            # If Docker not available, copy resume files to local directory
            if [ -d "$TEMP_DIR/volumes/resume_storage" ]; then
                echo "🔄 Copying resume files to local directory..." | tee -a "$RESTORE_LOG"
                mkdir -p ./backend/app/resumes
                cp -r "$TEMP_DIR/volumes/resume_storage/"* ./backend/app/resumes/
                echo "✅ Resume files copied to local directory" >> "$RESTORE_LOG"
            fi
        fi
    else
        echo "⚠️ No volume data found in backup" | tee -a "$RESTORE_LOG"
    fi

    # Restore database
    if [ -f "$TEMP_DIR/database_dump/resumeai.sql" ]; then
        echo "🔄 Restoring PostgreSQL database..." | tee -a "$RESTORE_LOG"
        
        if command -v docker &> /dev/null && [ "$(docker ps | grep '_db')" ]; then
            # Find the running database container
            if [ "$(docker ps | grep resumeai_db)" ]; then
                container_name=$(docker ps | grep resumeai_db | awk '{print $NF}')
            else
                container_name=$(docker ps | grep '_db' | head -1 | awk '{print $NF}')
            fi
            
            if [ -n "$container_name" ]; then
                echo "🔄 Restoring database to container $container_name..." | tee -a "$RESTORE_LOG"
                
                # Stop current database
                echo "🛑 Stopping database to ensure clean restore..." | tee -a "$RESTORE_LOG"
                docker stop $container_name
                
                # Start database again
                echo "🔄 Starting database container again..." | tee -a "$RESTORE_LOG"
                docker start $container_name
                
                # Wait for database to be ready
                echo "⏳ Waiting for database to be ready..." | tee -a "$RESTORE_LOG"
                sleep 5
                
                # Drop and recreate database
                echo "🔄 Dropping and recreating database..." | tee -a "$RESTORE_LOG"
                docker exec $container_name psql -U postgres -c "DROP DATABASE IF EXISTS resumeai;"
                docker exec $container_name psql -U postgres -c "CREATE DATABASE resumeai;"
                
                # Restore from SQL dump
                echo "🔄 Restoring from SQL dump..." | tee -a "$RESTORE_LOG"
                # Copy the dump into the container first
                docker cp "$TEMP_DIR/database_dump/resumeai.sql" $container_name:/tmp/resumeai.sql
                docker exec $container_name psql -U postgres -d resumeai -f /tmp/resumeai.sql
                
                echo "✅ Database restored" | tee -a "$RESTORE_LOG"
            else
                echo "⚠️ No database container found" | tee -a "$RESTORE_LOG"
            fi
        elif command -v psql &> /dev/null; then
            # Try direct restoration using psql
            echo "🔄 Attempting direct database restoration with psql..." | tee -a "$RESTORE_LOG"
            
            # Try to use environment variables if set
            PG_HOST=${PG_HOST:-localhost}
            PG_PORT=${PG_PORT:-5432}
            PG_USER=${PG_USER:-postgres}
            PG_PASSWORD=${PG_PASSWORD:-postgres}
            PG_DATABASE=${PG_DATABASE:-resumeai}
            
            # Export password for psql
            export PGPASSWORD="$PG_PASSWORD"
            
            # Drop and recreate database
            echo "🔄 Dropping and recreating database..." | tee -a "$RESTORE_LOG"
            psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -c "DROP DATABASE IF EXISTS $PG_DATABASE;" postgres
            psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -c "CREATE DATABASE $PG_DATABASE;" postgres
            
            # Restore from SQL dump
            echo "🔄 Restoring from SQL dump..." | tee -a "$RESTORE_LOG"
            psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DATABASE" -f "$TEMP_DIR/database_dump/resumeai.sql"
            
            if [ $? -eq 0 ]; then
                echo "✅ Database restored directly via psql" | tee -a "$RESTORE_LOG"
            else
                echo "⚠️ Direct database restoration failed" | tee -a "$RESTORE_LOG"
            fi
            
            # Unset password
            unset PGPASSWORD
        else
            echo "⚠️ Neither Docker database container nor psql found - can't restore database" | tee -a "$RESTORE_LOG"
            echo "📋 SQL dump is available at $TEMP_DIR/database_dump/resumeai.sql" | tee -a "$RESTORE_LOG"
            
            # Save the SQL dump for manual restoration
            mkdir -p ./database_restore
            cp "$TEMP_DIR/database_dump/resumeai.sql" ./database_restore/
            echo "📋 A copy of the SQL dump has been saved to ./database_restore/resumeai.sql" | tee -a "$RESTORE_LOG"
        fi
    else
        echo "⚠️ No database dump found in backup" | tee -a "$RESTORE_LOG"
    fi

    # Clean up temporary directory
    rm -rf "$TEMP_DIR"

    echo "✅ Restore completed!" | tee -a "$RESTORE_LOG"
    echo "You can now start the application using:" | tee -a "$RESTORE_LOG"
    echo "  - Docker mode: ./manage.sh docker-up" | tee -a "$RESTORE_LOG"
    echo "  - Local mode: ./manage.sh backend" | tee -a "$RESTORE_LOG"
    echo "" | tee -a "$RESTORE_LOG"
    echo "📝 Restore log saved to: $RESTORE_LOG" | tee -a "$RESTORE_LOG"
    
    echo "
📋 Restoration Summary
=====================
✅ Backup file: $BACKUP_FILE
✅ Restore log: $RESTORE_LOG
✅ Restored: $(date)

Next Steps:
1. Start the application:
   - Docker mode: ./manage.sh docker-up
   - Local mode: ./manage.sh backend

2. Verify the application is working:
   - Check backend API: http://localhost:8008/
   - Access frontend: http://localhost:3000/

3. If the database wasn't restored automatically:
   - A copy of the SQL dump was saved to ./database_restore/resumeai.sql
   - You can manually restore it using pgAdmin or the command line
"
}

# Function to initialize the database
init_database() {
    echo "🔄 Initializing PostgreSQL database for ResumeAI..."

    # Activate virtual environment
    activate_venv
    echo "✅ Virtual environment activated"

    # Check if we're running in Docker
    if [ "$1" == "docker" ]; then
        echo "✅ Running in Docker environment"
        # Use Docker environment variables
        export PG_HOST=${PG_HOST:-db}
    else
        echo "ℹ️ Running in local environment"
        # Use local environment variables
        export PG_HOST=${PG_HOST:-localhost}
    fi

    # Set other default environment variables if not set
    export PG_PORT=${PG_PORT:-5432}
    export PG_USER=${PG_USER:-postgres}
    export PG_PASSWORD=${PG_PASSWORD:-postgres}
    export PG_DATABASE=${PG_DATABASE:-resumeai}

    echo "ℹ️ Using database: ${PG_HOST}:${PG_PORT}/${PG_DATABASE}"

    # Run the initialization script
    cd backend
    python -m app.db_init --init --test-data --test-search

    # Check the exit code
    if [ $? -eq 0 ]; then
        echo "✅ Database initialization completed successfully!"
    else
        echo "❌ Database initialization failed!"
        exit 1
    fi

    echo "
You can now start the application with:
  - Backend: ./manage.sh backend
  - Frontend: ./manage.sh frontend
"
}

# Function to set up the application
setup_app() {
    echo "Setting up ResumeAI..."
    
    # Check if virtual environment exists, create if not
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python -m venv venv
    fi
    
    # Activate virtual environment
    activate_venv
    
    # Install backend dependencies
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
    
    # Install frontend dependencies
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    
    # Install Playwright browsers (if Playwright is installed)
    if pip list | grep -q "playwright"; then
        echo "Installing Playwright browsers..."
        playwright install chromium
    fi
    
    echo "Setup complete!"
    echo "You can now start the application with:"
    echo "  - Backend: ./manage.sh backend"
    echo "  - Frontend: ./manage.sh frontend"
}

# Function to start Docker services
docker_up() {
    echo "Starting Docker services..."
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        echo "Warning: No .env file found. Docker may fail due to missing environment variables."
        echo "Run './manage.sh config --template' to generate a template .env file."
    fi
    
    # Export environment variables from .env file for Docker Compose
    if [ -f ".env" ]; then
        echo "Exporting environment variables from .env file..."
        export $(grep -v '^#' .env | xargs)
    fi
    
    # Start Docker services
    docker compose up -d
    echo "Docker services started!"
    echo "You can check the status with: ./manage.sh check"
}

# Function to stop Docker services
docker_down() {
    echo "Stopping Docker services..."
    docker compose down
    echo "Docker services stopped!"
}

# Function to manage configuration
show_config() {
    echo "ResumeAI Configuration"
    echo "======================"
    
    # Activate virtual environment
    activate_venv
    
    # Parse arguments
    SECTION="all"
    OUTPUT_TEMPLATE=0
    
    while [ $# -gt 0 ]; do
        case "$1" in
            --section)
                SECTION="$2"
                shift 2
                ;;
            --template)
                OUTPUT_TEMPLATE=1
                shift
                ;;
            *)
                echo "Unknown option: $1"
                shift
                ;;
        esac
    done
    
    # Change to backend directory
    cd backend
    
    # Run the configuration info script
    if [ $OUTPUT_TEMPLATE -eq 1 ]; then
        python config_info.py --show template
    else
        python config_info.py --show "$SECTION"
    fi
}

# Main script logic
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

COMMAND=$1
shift

case $COMMAND in
    backend)
        start_backend
        ;;
    frontend)
        if [ "$1" == "--docker" ]; then
            start_frontend "docker"
        else
            start_frontend "local"
        fi
        ;;
    check)
        check_services
        ;;
    backup)
        create_backup
        ;;
    restore)
        restore_backup "$1"
        ;;
    init-db)
        if [ "$1" == "--docker" ]; then
            init_database "docker"
        else
            init_database "local"
        fi
        ;;
    setup)
        setup_app
        ;;
    config)
        show_config "$@"
        ;;
    docker-up)
        docker_up
        ;;
    docker-down)
        docker_down
        ;;
    help)
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac

exit 0