# ResumeAI - Resume & Vacancy Matching System

A full-stack application that automatically scrapes job vacancies, stores them in a database, and matches them with resumes using AI.

## Project Structure

- **backend/** - FastAPI backend
  - **app/** - Backend application code
    - **components/** - Shared components (NocoDB client, etc.)
    - **database/** - Database interfaces (SQLite, NocoDB)
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

- Scrape job listings from Spinweb
- Store vacancies in NocoDB or SQLite
- Process resumes and generate embeddings
- Match vacancies with resumes using vector similarity
- Evaluate matches using OpenAI GPT-4o-mini
- Interactive web dashboard to view and manage vacancies and resumes

## Setup

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

4. Set up your environment variables by copying `.env.example` to `.env`:

```bash
cp .env.example .env
```

5. Update the `.env` file with your credentials and configuration

6. Run the backend server:

```bash
cd backend
uvicorn main:app --reload
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

## API Endpoints

- `GET /api/vacancies` - Get all vacancies with pagination
- `GET /api/vacancies/{id}` - Get a specific vacancy
- `POST /api/vacancies` - Create a new vacancy
- `PUT /api/vacancies/{id}` - Update a vacancy
- `DELETE /api/vacancies/{id}` - Delete a vacancy
- `GET /api/resumes` - Get all resumes
- `GET /api/resumes/{id}` - Get a specific resume
- `POST /api/resumes` - Add a resume from JSON
- `POST /api/resumes/upload` - Upload a resume PDF file
- `GET /api/settings` - Get application settings
- `PUT /api/settings` - Update application settings

## Database Configuration

The system supports multiple database backends:

1. **SQLite** - Simple file-based database (default)
   - Set `DB_TYPE=sqlite` in `.env`
   - Set `SQLITE_DB_PATH=path/to/database.db` in `.env`

2. **NocoDB** - Web-based database with Airtable-like UI
   - Set `DB_TYPE=nocodb` in `.env`
   - Configure NocoDB credentials in `.env`

## Original CLI-Based System

The original CLI-based system is still available in the following directories:
- **01_OAS/** - OpenAI Resume Matching System (Airtable Version)
- **02_OCL/** - OpenAI Resume Matching System (Local Version)
- **03_ONS/** - OpenAI Resume Matching System (NocoDB Version)

To use the original system:

```bash
cd 03_ONS
python combined_process.py
```

## Troubleshooting

- For Playwright errors, try reinstalling the browsers:

```bash
playwright install
```

- For NocoDB errors, check if:
  - Your API token is correct
  - The URL, project, and table names are correct
  - The field names are correct (case-sensitive)

- For OpenAI errors, check if:
  - Your API key is correct
  - You have sufficient credits

## Author

- **Daniel Tromp**
- **Email:** drpgmtromp@gmail.com
- **Version:** 2.0.0
- **License:** MIT
- **Repository:** https://github.com/DanielTromp/ResumeAI