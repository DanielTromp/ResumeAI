# ResumeAI - Resume & Vacancy Matching System

A full-stack application that automatically scrapes job vacancies, stores them in a database, and matches them with resumes using AI.

## Project Structure

- **backend/** - FastAPI backend
  - **app/** - Backend application code
    - **components/** - Shared components
    - **database/** - Database interfaces (PostgreSQL)
    - **models/** - Pydantic data models
    - **routers/** - API route definitions
    - **services/** - Business logic services
    - **resumes/** - PDF resume storage
  - **main.py** - FastAPI application entry point
  - **requirements.txt** - Backend dependencies

- **frontend/** - React frontend
  - **src/** - React source code
    - **components/** - Reusable UI components
    - **pages/** - Page components
    - **App.js** - Main React component
    - **index.js** - React entry point

## Features

- **Resume Management**
  - Upload and manage PDF resumes
  - View resumes directly in the browser
  - Select specific resumes for processing
  - Download and delete resumes as needed

- **Vacancy Management**
  - Scrape job listings from Spinweb
  - Store vacancies in PostgreSQL database
  - Filter and search through vacancies
  - View detailed vacancy information

- **AI Matching**
  - Process resumes and generate embeddings
  - Match vacancies with resumes using vector similarity
  - Evaluate matches using OpenAI GPT-4o-mini
  - Customize matching prompt templates

- **Task Management**
  - Track bugs, features, and improvements
  - Assign priorities (Low, Medium, High, Critical)
  - Track status (Todo, In Progress, Done)
  - Reference tasks by ID

- **UI Features**
  - Dark/Light theme support
  - Responsive design
  - Interactive dashboard
  - Process monitoring and execution

## Setup

For detailed installation instructions, see the [Installation Guide](CLAUDE.md).

### Backend

1. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install the required packages:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Run the backend server:
   ```bash
   cd backend
   python main.py
   ```

### Frontend

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

## Key Commands

### Management Script
The `./manage.sh` script provides a unified interface for all operations:
```bash
./manage.sh help              # Show all available commands
./manage.sh backend           # Start backend server
./manage.sh frontend          # Start frontend development server
./manage.sh docker-up         # Start all services via Docker
./manage.sh docker-down       # Stop Docker services
./manage.sh init-db           # Initialize PostgreSQL database
./manage.sh backup            # Create application backup
./manage.sh restore <file>    # Restore from backup
./manage.sh setup             # Set up the application (activate venv, install deps)
./manage.sh check             # Check running services
```

## Core Process Flow

The scheduled process runs through these sequential steps:

1. **Resume Import & Vectorization**
   - Imports resume files from the resumes directory
   - Extracts text content from PDFs and other formats
   - Generates vector embeddings via OpenAI API
   - Stores in PostgreSQL with pgvector extension

2. **Vacancy Scraping**
   - Uses Playwright to scrape job vacancies from configured sources
   - Parses vacancy details (requirements, descriptions, etc.)
   - Saves structured data to database

3. **Resume-Vacancy Matching**
   - Compares resume embeddings with vacancy requirements
   - Calculates similarity scores using vector operations
   - Identifies best matches based on configured thresholds

4. **AI Analysis**
   - Analyzes matches using GPT-4o-mini
   - Generates recommendations and insights
   - Evaluates fit between candidates and positions

5. **Database Storage**
   - Writes all results to PostgreSQL
   - Updates match scores and recommendations
   - Maintains historical data for tracking

## API Endpoints

### Vacancies
- `GET /api/vacancies` - Get all vacancies with pagination
- `GET /api/vacancies/{id}` - Get a specific vacancy
- `POST /api/vacancies` - Create a new vacancy
- `PUT /api/vacancies/{id}` - Update a vacancy
- `DELETE /api/vacancies/{id}` - Delete a vacancy

### Resumes
- `GET /api/resumes` - Get all resumes
- `GET /api/resumes/{id}` - Get a specific resume
- `POST /api/resumes` - Add a resume from JSON
- `POST /api/resumes/upload` - Upload a resume PDF file
- `GET /api/resumes/download/{filename}` - Download a resume
- `DELETE /api/resumes/{name}` - Delete a resume

### Tasks
- `GET /api/tasks` - Get all tasks with pagination and filtering
- `GET /api/tasks/{id}` - Get a specific task
- `POST /api/tasks` - Create a new task
- `PUT /api/tasks/{id}` - Update a task
- `DELETE /api/tasks/{id}` - Delete a task

### Settings & Process
- `GET /api/settings` - Get application settings
- `PUT /api/settings` - Update application settings
- `POST /api/process/start` - Run the matching process
- `GET /api/process/status` - Get process status

## Backup and Restore Guide

This document provides a comprehensive guide on backing up and restoring your ResumeAI application.

### Quick Reference

```bash
# Create a full backup
./manage.sh backup

# Create a lightweight backup (excludes node_modules and other large directories)
# Recommended for Raspberry Pi or systems with limited storage
./manage.sh backup --light

# Create a backup excluding just node_modules
./manage.sh backup --exclude-node-modules

# Restore from a backup
./manage.sh restore backups/resumeai_backup_20250310_123456.tar.gz
```

### Backup System Overview

The ResumeAI backup system creates comprehensive backups of:

1. **Code** - All application code (backend and frontend)
2. **Configuration** - Environment variables and Docker configurations
3. **Database** - PostgreSQL database dump
4. **Files** - Resume PDFs and other data files
5. **Docker Volumes** - Data from Docker volumes (when running in Docker mode)

Each backup is a self-contained archive that can fully restore your application to the state it was in when the backup was created.

### Creating Backups

#### Backup Types

##### Full Backup

To create a complete backup of everything (code, database, configuration, files):
```bash
./manage.sh backup
```

##### Lightweight Backup (for Raspberry Pi or low-storage systems)

To create a backup that excludes node_modules and other large directories:
```bash
./manage.sh backup --light
```

This creates a much smaller backup file that:
- Excludes node_modules directories
- Excludes build directories
- Excludes Python cache files
- Still includes all source code, configuration, and database dumps

##### Backup Without Node Modules

If you just want to exclude the node_modules directories:
```bash
./manage.sh backup --exclude-node-modules
```

This will:
- Back up all code from backend and frontend directories
- Export database to SQL dump
- Back up configuration files (.env files)
- Back up all resume files
- Back up Docker volumes (if Docker is running)
- Create a detailed backup log

The backup will be stored in the `backups/` directory with a timestamp in the filename.

### Restoring from Backups

#### Standard Restore

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

### Verification After Restore

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

## Development Setup

This document provides instructions for setting up the ResumeAI development environment, addressing network connectivity issues between Docker containers.

### Simplified Development Approach

Due to networking issues between frontend and backend Docker containers, we recommend a hybrid approach:

1. Run the backend in Docker (for isolation and dependencies)
2. Run the frontend directly on your host machine (for better network connectivity)

### Setup Instructions

#### Step 1: Start the Backend Container

```bash
# Start only the backend services
docker compose -f docker-compose.simple.yml up -d
```

This will start the backend API on http://localhost:8008.

#### Step 2: Run the Frontend Directly

```bash
# Execute the frontend setup script
./setup-frontend.sh
```

This script will:
1. Change to the frontend directory
2. Update the proxy configuration to point to http://localhost:8008
3. Start the React development server

The frontend will be available at http://localhost:3000 and will communicate with the backend at http://localhost:8008.

### Why This Approach?

Docker networking between containers can be complex and varies across different host operating systems. Running the frontend directly on the host machine eliminates these networking issues while still providing a good development experience with:

- Hot module reloading for the frontend
- Clean containerization for the backend
- Consistent access to the backend API

### Backup and Restore

The backup and restore scripts still work with this hybrid setup:

```bash
# Create a backup
./backup.sh

# Restore from a backup
./restore.sh ./backups/resumeai_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Production Deployment

For production, you can still use the full Docker Compose setup with both frontend and backend containers, as networking issues are typically more predictable in production environments.

## Code Review Recommendations

This document contains recommendations for improving the ResumeAI codebase by identifying and addressing redundant components, unused modules, and other code efficiency opportunities.

### 1. DONE - Redundant Requirements Files

**Issue**: Multiple requirements files exist across the project, leading to potential version conflicts and maintenance challenges.

- `/requirements.txt`
- `/backend/requirements.txt`
- `/backend/app/requirements.txt`

**Recommendation**: 
- Consolidate into a single `requirements.txt` in the project root
- Use separate requirements files only if there are distinct deployment environments (e.g., `requirements-dev.txt`, `requirements-prod.txt`)
- Ensure consistent versioning across files if separate files must be maintained

### 2. DONE - Shell Script Optimization

**Issue**: Several shell scripts with overlapping functionality:

- `restart-backend.sh` and `restart-frontend.sh` - Basic restart scripts
- `check-containers.sh` - Container status check
- `backup.sh` and `restore.sh` - Data management
- `setup-frontend.sh` - Frontend setup
- `init-postgres.sh` - Database initialization

**Recommendation**:
- Consolidate into a single management script with arguments: `./manage.sh [backend|frontend|check|backup|restore]`
- Add a simple help command: `./manage.sh help`
- Create simple documentation for the script usage

### 3. DONE - Docker Configuration Files

**Issue**: Multiple Docker configuration files:
- `docker-compose.yml`
- `docker-compose.simple.yml`

**Recommendation**:
- Keep only `docker-compose.yml` as the main configuration
- If different configurations are needed, use Docker Compose profiles instead of separate files
- Consider using Docker Compose overrides for environment-specific settings

### 4. DONE - Potential Unused Python Modules

**Issue**: Several libraries in requirements files may not be actively used:

- `geopy` - Geographic distance calculations library
- `fake-useragent` - May not be necessary if using Playwright
- `pillow` - Image processing library that may be unused
- `schedule` - Simple scheduler that's now replaced with custom scheduling

**Recommendation**:
- Review imports across the codebase to confirm which libraries are actually used
- Remove unused dependencies from requirements files
- Document essential dependencies with comments explaining their purpose

### 5. DONE - Configuration Management

**Issue**: Multiple configuration approaches:
- `.env` files in multiple locations
- `config.py` files
- Command-line arguments

**Recommendation**:
- Standardize on a single configuration approach
- Create a hierarchical configuration system: defaults → config files → environment variables → command-line arguments
- Implement proper validation for all configuration values

### 6. API Authentication

**Issue**: The `BasicAuthMiddleware` in `backend/main.py` is defined but commented out with authentication handled in alternative ways.

**Recommendation**:
- Remove unused middleware code if not actively used
- Document the current authentication mechanism
- Consider implementing a more robust authentication system (e.g., JWT tokens)

### 7. Database Interface Redundancy

**Issue**: Multiple database interfaces and management classes:
- PostgreSQL-specific code in multiple locations
- Vector database functionality spread across files

**Recommendation**:
- Create a unified database abstraction layer
- Consolidate database management code
- Document database schema and relationships

### 8. Frontend Components

**Issue**: Potential unused components in the frontend React application.

**Recommendation**:
- Run a dead code analysis tool on the frontend code
- Remove unused components and functions
- Consider implementing code splitting for better performance

### 9. Logging Standardization

**Issue**: Multiple logging approaches and log files:
- `spinweb_scraper.log`
- `scraper.log`
- Various logging handlers in different modules

**Recommendation**:
- Implement a standardized logging strategy across the application
- Use a logging configuration file
- Consider a more sophisticated logging solution for production

### 10. Documentation Updates

**Issue**: Multiple README files with overlapping information:
- `README.md`
- `README-POSTGRES.md`
- `README-SOLUTION.md`
- `CLAUDE.md`

**Recommendation**:
- Consolidate documentation into a single comprehensive README with clear sections
- Move specialized documentation to a `/docs` directory
- Create a simple getting started guide for new developers

### 11. Sensitive Data Management

**Issue**: Sensitive data such as API keys, tokens, and passwords are present in the `.env` files and may have been committed to the repository in the past.

**Recommendation**:
- Ensure that `.env` files are added to `.gitignore` before committing any sensitive data
- Remove any committed sensitive data from the Git history using tools like `git filter-branch` or `BFG Repo-Cleaner`
- Rotate all exposed credentials immediately
- Consider using a secrets management tool (e.g., Docker Secrets, HashiCorp Vault, AWS Secrets Manager) to securely manage sensitive data

### 12. Code Formatting and Linting

**Issue**: Inconsistent code formatting across the project can lead to readability and maintenance issues.

**Recommendation**:
- Implement code formatting tools such as Prettier (for JavaScript/React) and Black or Flake8 (for Python)
- Add configuration files (e.g., `.prettierrc`, `.flake8`) and include linting in the CI/CD pipeline
- Enforce code style standards through pre-commit hooks

### 13. CI/CD Pipeline Improvements

**Issue**: The current deployment and testing processes may not be fully automated, leading to potential human errors and inconsistencies.

**Recommendation**:
- Implement a continuous integration/continuous deployment (CI/CD) pipeline using tools such as GitHub Actions, Jenkins, or GitLab CI
- Automate testing, linting, and dependency vulnerability scanning within the pipeline
- Use Docker and container orchestration to streamline deployments
- Ensure that environment-specific configurations and secrets are managed securely in the pipeline

### Action Plan

1. **Immediate Improvements**:
   - Consolidate requirements files
   - Remove unused shell scripts
   - Update `.gitignore` to exclude all temporary files

2. **Short-term Improvements**:
   - Standardize configuration management
   - Clean up authentication code
   - Remove dead code from frontend

3. **Long-term Improvements**:
   - Refactor database interfaces
   - Implement comprehensive logging strategy
   - Consolidate documentation
   - Enhance security practices and automate CI/CD processes

### Conclusion

The ResumeAI project has a solid foundation but contains several opportunities for codebase optimization. By addressing these redundancies and organizational issues, the project will become more maintainable, easier to understand for new developers, and more efficient to deploy and operate.

## Author

- **Daniel Tromp**
- **Email:** drpgmtromp@gmail.com
- **Version:** 2.0.0
- **License:** MIT
- **Repository:** [GitHub Repository](https://github.com/DanielTromp/ResumeAI)