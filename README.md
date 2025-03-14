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

3. Install Playwright browsers:

```bash
playwright install
```

4. Run the backend server:

```bash
cd backend
python main.py
```

The backend will start on http://localhost:8008 by default.

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

The frontend will start on http://localhost:3000 by default.

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
- `POST /api/process/run` - Run the matching process
- `GET /api/process/status` - Get process status

## Database Configuration

The system uses PostgreSQL with pgvector for storing resumes and vacancy data:

- Configure the PostgreSQL connection in `.env`:
  ```
  PG_HOST=localhost
  PG_PORT=5432
  PG_USER=postgres
  PG_PASSWORD=postgres
  PG_DATABASE=resumeai
  ```

- For Docker deployment, the settings are preconfigured to connect to the PostgreSQL container.

## Deployment

ResumeAI can be deployed in both development and production environments.

### Development Environment
Follow the [Setup](#setup) instructions to run the application locally for development.

> **Important Note:** The frontend requires Node.js 18.x or higher. Using an older version will cause compatibility warnings and may lead to issues.

### Docker Deployment

A Docker Compose setup is included for easy development and deployment.

#### Prerequisites

- Docker and Docker Compose installed
- Git for cloning the repository

#### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/YourUsername/ResumeAI.git
   cd ResumeAI
   ```

2. Start the development environment:
   ```bash
   docker compose up -d
   ```

3. Access the applications:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8008
   - API Docs: http://localhost:8008/docs

#### Hot Reloading

The development setup includes hot reloading for both frontend and backend:

- Frontend changes will automatically refresh in the browser
- Backend changes will automatically restart the FastAPI server

### Backup and Restore

#### Creating a Backup

Use the included backup script:

```bash
# Make the script executable (first time only)
chmod +x backup.sh

# Create a backup
./backup.sh
```

Backups are stored in the `./backups` directory.

#### Restoring from Backup

Use the included restore script:

```bash
# Make the script executable (first time only)
chmod +x restore.sh

# Restore from a backup file
./restore.sh ./backups/resumeai_backup_20250304_123456.tar.gz
```

### Migrating to Another System

To migrate the application to another system:

1. Create a backup on the source system:
   ```bash
   ./backup.sh
   ```

2. Transfer the backup file to the target system (using scp, rsync, etc.)

3. Clone the repository on the target system:
   ```bash
   git clone https://github.com/YourUsername/ResumeAI.git
   cd ResumeAI
   ```

4. Restore from the transferred backup:
   ```bash
   ./restore.sh path/to/backup_file.tar.gz
   ```

5. Start the application:
   ```bash
   docker compose up -d
   ```

### Without GitHub

If you need to deploy without GitHub:

1. Create a backup on the source system that includes all code and data:
   ```bash
   ./backup.sh
   ```

2. Transfer the backup file to the target system

3. On the target system, create a new directory for the application:
   ```bash
   mkdir ResumeAI
   cd ResumeAI
   ```

4. Copy the restore script from the source system or create it manually

5. Restore from the backup:
   ```bash
   ./restore.sh path/to/backup_file.tar.gz
   ```

6. Install Docker and Docker Compose if not already installed

7. Start the application:
   ```bash
   docker compose up -d
   ```

### Production Environment
For additional production deployment options, see the detailed [Production Deployment Guide](CLAUDE.md#production-deployment-guide) which includes:

- Backend deployment with Gunicorn
- Frontend deployment with Nginx
- Security considerations 
- Monitoring and maintenance

## Troubleshooting

- For Playwright errors, try reinstalling the browsers:

```bash
playwright install
```

- For PostgreSQL errors, check if:
  - Your connection details are correct
  - The database and tables exist
  - PostgreSQL is running and accessible

- For OpenAI errors, check if:
  - Your API key is correct
  - You have sufficient credits

- For port conflicts:
  - Change the backend port in `main.py` and the proxy in `frontend/package.json`
  - Default ports: Backend (8008), Frontend (3000)

- For Node.js version warnings:
  - Upgrade to Node.js 18.x or higher (`nvm install 18`)
  - Reinstall dependencies (`rm -rf node_modules package-lock.json && npm install`)

- For security vulnerabilities:
  - Run `npm audit fix` to fix compatible vulnerabilities
  - For critical vulnerabilities, try `npm audit fix --force` (may require manual intervention)

## Author

- **Daniel Tromp**
- **Email:** drpgmtromp@gmail.com
- **Version:** 2.0.0
- **License:** MIT
- **Repository:** https://github.com/DanielTromp/ResumeAI

