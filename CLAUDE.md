# ResumeAI Project Guidelines

## Commands
- **Run Combined Process:** `cd 03_ONS && python combined_process.py`
- **Install Dependencies:** `pip install -r requirements.txt`
- **Install Playwright:** `playwright install`
- **Activate Virtual Environment:** `source venv/bin/activate` (Mac/Linux) or `.\venv\Scripts\activate` (Windows)

## Code Style Guidelines
- **Imports:** Group in order: standard library, third-party, project-specific
- **Docstrings:** Use """triple quotes""" with function description, parameters, and return values
- **Error Handling:** Use try/except with specific exception types and logging
- **Logging:** Use the progress_logger for user feedback and standard logger for errors
- **Naming:** Use snake_case for variables/functions, CamelCase for classes
- **Environment Variables:** Store sensitive data in .env file, load with python-dotenv

## Project Structure
- **03_ONS:** Latest version using NocoDB backend
- **02_OCL:** Version using local storage (LanceDB)
- **01_OAS:** Version using Airtable backend

## Key Dependencies
- OpenAI API for embeddings and matching (GPT-4o-mini)
- Playwright for web scraping
- Supabase for vector storage
- NocoDB for vacancy storage and tracking