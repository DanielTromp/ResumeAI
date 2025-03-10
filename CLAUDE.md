# ResumeAI Development Guidelines

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

### Backend
```bash
source venv/bin/activate      # Activate virtual environment
cd backend && python main.py  # Start backend server
python -m app.combined_process # Run the combined process
```

### Frontend
```bash
cd frontend && npm install    # Install dependencies
cd frontend && npm start      # Start development server
cd frontend && npm test       # Run frontend tests
cd frontend && npm run build  # Create production build
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

This process is triggered by the scheduler service at configured intervals or can be run manually via the API.

## Code Style Guidelines

### Python
- **Imports:** Group in order: standard library, third-party, project-specific
- **Docstrings:** Use """triple quotes""" with function description, params, returns
- **Naming:** snake_case for variables/functions, CamelCase for classes
- **Error Handling:** Use try/except with specific exceptions and proper logging
- **Logging:** progress_logger for user feedback, standard logger for errors
- **Configuration:** Use centralized config system instead of direct env vars

### JavaScript/React
- **Component Structure:** Functional components with hooks preferred
- **State Management:** Use React context for global state
- **API Calls:** Use the utilities in src/utils/api.js

## Project Architecture
- **Backend:** FastAPI with PostgreSQL + pgvector 
- **Frontend:** React with Material UI
- **Configuration:** Hierarchical system (command args > env vars > defaults)
- **Database:** PostgreSQL with pgvector extension for vector similarity search
- **AI Integration:** OpenAI API (GPT-4o-mini) for embeddings and matching

## Key Dependencies
- OpenAI API for embeddings and matching
- Playwright for web scraping
- PostgreSQL with pgvector for database storage
- React for frontend UI