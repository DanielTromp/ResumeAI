# ResumeAI Integrated Frontend Setup

The React frontend has been integrated directly into the FastAPI backend for simplified deployment.

## Benefits

- Eliminates network connectivity issues between frontend and backend
- Simplifies deployment (only one container needed)
- Reduces resource usage
- Better performance on Raspberry Pi and other low-power devices

## How It Works

1. The React frontend is built as a static site
2. The built files are served directly by FastAPI
3. All API requests use relative paths (/api/...)
4. FastAPI handles both the API and serving the frontend files

## Updating the Frontend

If you make changes to the frontend code:

1. Edit the files in the frontend directory
2. Rebuild the frontend:
   
> resumeai-frontend@0.1.0 build
> react-scripts build

Creating an optimized production build...
Compiled with warnings.

[eslint] 
src/App.js
  Line 1:51:  'useEffect' is defined but never used  no-unused-vars

src/pages/Dashboard.js
  Line 125:6:  React Hook useEffect has a missing dependency: 'stats'. Either include it or remove the dependency array. You can also do a functional update 'setStats(s => ...)' if you only need 'stats' in the 'setStats' call  react-hooks/exhaustive-deps

src/pages/NotFound.js
  Line 3:41:  'Box' is defined but never used  no-unused-vars

src/pages/ProcessRunner.js
  Line 11:3:  'TextField' is defined but never used                                                                               no-unused-vars
  Line 15:3:  'Grid' is defined but never used                                                                                    no-unused-vars
  Line 61:6:  React Hook useEffect has a missing dependency: 'pollingInterval'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/pages/TaskBoard.js
  Line 44:8:   'RefreshIcon' is defined but never used                                                                        no-unused-vars
  Line 105:6:  React Hook useEffect has a missing dependency: 'fetchTasks'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

Search for the keywords to learn more about each warning.
To ignore, add // eslint-disable-next-line to the line before.

File sizes after gzip:

  179.67 kB  build/static/js/main.bef51acd.js

The project was built assuming it is hosted at /.
You can control this with the homepage field in your package.json.

The build folder is ready to be deployed.
You may serve it with a static server:

  npm install -g serve
  serve -s build

Find out more about deployment here:

  https://cra.link/deployment
3. Restart the backend:
   Debug: Command is 'backend', remaining args: ''
Starting backend service...
No virtual environment found. Consider creating one with: python -m venv venv
Looking in indexes: https://pypi.org/simple, https://www.piwheels.org/simple
Requirement already satisfied: fastapi>=0.104.0 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 2)) (0.115.11)
Requirement already satisfied: uvicorn>=0.23.2 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 3)) (0.34.0)
Requirement already satisfied: pydantic>=2.4.2 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 4)) (2.10.6)
Requirement already satisfied: python-dotenv>=1.0.0 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 5)) (1.0.1)
Requirement already satisfied: python-multipart>=0.0.6 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 6)) (0.0.20)
Requirement already satisfied: psycopg2-binary>=2.9.9 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 9)) (2.9.10)
Requirement already satisfied: pgvector>=0.2.0 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 10)) (0.3.6)
Requirement already satisfied: beautifulsoup4>=4.13.0 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 13)) (4.13.3)
Requirement already satisfied: playwright>=1.50.0 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 14)) (1.50.0)
Requirement already satisfied: html2text>=2024.2.26 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 15)) (2024.2.26)
Requirement already satisfied: Crawl4AI>=0.4.248 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 16)) (0.5.0.post4)
Requirement already satisfied: lxml in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 17)) (5.3.1)
Requirement already satisfied: openai>=1.3.0 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 20)) (1.65.5)
Requirement already satisfied: tiktoken>=0.8.0 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 21)) (0.9.0)
Requirement already satisfied: pypdf>=5.3.0 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 24)) (5.3.1)
Requirement already satisfied: PyPDF2>=3.0.1 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 25)) (3.0.1)
Requirement already satisfied: aiohttp>=3.11.0 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 28)) (3.11.13)
Requirement already satisfied: requests>=2.31.0 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 29)) (2.32.3)
Requirement already satisfied: numpy>=2.2.2 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 30)) (2.2.3)
Requirement already satisfied: tqdm>=4.66.1 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 31)) (4.67.1)
Requirement already satisfied: rich in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 32)) (13.9.4)
Requirement already satisfied: PyYAML in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 33)) (6.0.2)
Requirement already satisfied: schedule>=1.2.0 in ./backend/venv/lib/python3.11/site-packages (from -r requirements.txt (line 36)) (1.2.2)
Requirement already satisfied: starlette<0.47.0,>=0.40.0 in ./backend/venv/lib/python3.11/site-packages (from fastapi>=0.104.0->-r requirements.txt (line 2)) (0.46.1)
Requirement already satisfied: typing-extensions>=4.8.0 in ./backend/venv/lib/python3.11/site-packages (from fastapi>=0.104.0->-r requirements.txt (line 2)) (4.12.2)
Requirement already satisfied: click>=7.0 in ./backend/venv/lib/python3.11/site-packages (from uvicorn>=0.23.2->-r requirements.txt (line 3)) (8.1.8)
Requirement already satisfied: h11>=0.8 in ./backend/venv/lib/python3.11/site-packages (from uvicorn>=0.23.2->-r requirements.txt (line 3)) (0.14.0)
Requirement already satisfied: annotated-types>=0.6.0 in ./backend/venv/lib/python3.11/site-packages (from pydantic>=2.4.2->-r requirements.txt (line 4)) (0.7.0)
Requirement already satisfied: pydantic-core==2.27.2 in ./backend/venv/lib/python3.11/site-packages (from pydantic>=2.4.2->-r requirements.txt (line 4)) (2.27.2)
Requirement already satisfied: soupsieve>1.2 in ./backend/venv/lib/python3.11/site-packages (from beautifulsoup4>=4.13.0->-r requirements.txt (line 13)) (2.6)
Requirement already satisfied: pyee<13,>=12 in ./backend/venv/lib/python3.11/site-packages (from playwright>=1.50.0->-r requirements.txt (line 14)) (12.1.1)
Requirement already satisfied: greenlet<4.0.0,>=3.1.1 in ./backend/venv/lib/python3.11/site-packages (from playwright>=1.50.0->-r requirements.txt (line 14)) (3.1.1)
Requirement already satisfied: aiosqlite~=0.20 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (0.21.0)
Requirement already satisfied: litellm>=1.53.1 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (1.63.3)
Requirement already satisfied: pillow~=10.4 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (10.4.0)
Requirement already satisfied: tf-playwright-stealth>=1.1.0 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (1.1.2)
Requirement already satisfied: xxhash~=3.4 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (3.5.0)
Requirement already satisfied: rank-bm25~=0.2 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (0.2.2)
Requirement already satisfied: aiofiles>=24.1.0 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (24.1.0)
Requirement already satisfied: colorama~=0.4 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (0.4.6)
Requirement already satisfied: snowballstemmer~=2.2 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (2.2.0)
Requirement already satisfied: pyOpenSSL>=24.3.0 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (25.0.0)
Requirement already satisfied: psutil>=6.1.1 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (7.0.0)
Requirement already satisfied: nltk>=3.9.1 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (3.9.1)
Requirement already satisfied: cssselect>=1.2.0 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (1.3.0)
Requirement already satisfied: httpx>=0.27.2 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (0.28.1)
Requirement already satisfied: fake-useragent>=2.0.3 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (2.0.3)
Requirement already satisfied: pyperclip>=1.8.2 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (1.9.0)
Requirement already satisfied: faust-cchardet>=2.1.19 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (2.1.19)
Requirement already satisfied: humanize>=4.10.0 in ./backend/venv/lib/python3.11/site-packages (from Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (4.12.1)
Requirement already satisfied: anyio<5,>=3.5.0 in ./backend/venv/lib/python3.11/site-packages (from openai>=1.3.0->-r requirements.txt (line 20)) (4.8.0)
Requirement already satisfied: distro<2,>=1.7.0 in ./backend/venv/lib/python3.11/site-packages (from openai>=1.3.0->-r requirements.txt (line 20)) (1.9.0)
Requirement already satisfied: jiter<1,>=0.4.0 in ./backend/venv/lib/python3.11/site-packages (from openai>=1.3.0->-r requirements.txt (line 20)) (0.8.2)
Requirement already satisfied: sniffio in ./backend/venv/lib/python3.11/site-packages (from openai>=1.3.0->-r requirements.txt (line 20)) (1.3.1)
Requirement already satisfied: regex>=2022.1.18 in ./backend/venv/lib/python3.11/site-packages (from tiktoken>=0.8.0->-r requirements.txt (line 21)) (2024.11.6)
Requirement already satisfied: aiohappyeyeballs>=2.3.0 in ./backend/venv/lib/python3.11/site-packages (from aiohttp>=3.11.0->-r requirements.txt (line 28)) (2.5.0)
Requirement already satisfied: aiosignal>=1.1.2 in ./backend/venv/lib/python3.11/site-packages (from aiohttp>=3.11.0->-r requirements.txt (line 28)) (1.3.2)
Requirement already satisfied: attrs>=17.3.0 in ./backend/venv/lib/python3.11/site-packages (from aiohttp>=3.11.0->-r requirements.txt (line 28)) (25.1.0)
Requirement already satisfied: frozenlist>=1.1.1 in ./backend/venv/lib/python3.11/site-packages (from aiohttp>=3.11.0->-r requirements.txt (line 28)) (1.5.0)
Requirement already satisfied: multidict<7.0,>=4.5 in ./backend/venv/lib/python3.11/site-packages (from aiohttp>=3.11.0->-r requirements.txt (line 28)) (6.1.0)
Requirement already satisfied: propcache>=0.2.0 in ./backend/venv/lib/python3.11/site-packages (from aiohttp>=3.11.0->-r requirements.txt (line 28)) (0.3.0)
Requirement already satisfied: yarl<2.0,>=1.17.0 in ./backend/venv/lib/python3.11/site-packages (from aiohttp>=3.11.0->-r requirements.txt (line 28)) (1.18.3)
Requirement already satisfied: charset-normalizer<4,>=2 in ./backend/venv/lib/python3.11/site-packages (from requests>=2.31.0->-r requirements.txt (line 29)) (3.4.1)
Requirement already satisfied: idna<4,>=2.5 in ./backend/venv/lib/python3.11/site-packages (from requests>=2.31.0->-r requirements.txt (line 29)) (3.10)
Requirement already satisfied: urllib3<3,>=1.21.1 in ./backend/venv/lib/python3.11/site-packages (from requests>=2.31.0->-r requirements.txt (line 29)) (2.3.0)
Requirement already satisfied: certifi>=2017.4.17 in ./backend/venv/lib/python3.11/site-packages (from requests>=2.31.0->-r requirements.txt (line 29)) (2025.1.31)
Requirement already satisfied: markdown-it-py>=2.2.0 in ./backend/venv/lib/python3.11/site-packages (from rich->-r requirements.txt (line 32)) (3.0.0)
Requirement already satisfied: pygments<3.0.0,>=2.13.0 in ./backend/venv/lib/python3.11/site-packages (from rich->-r requirements.txt (line 32)) (2.19.1)
Requirement already satisfied: httpcore==1.* in ./backend/venv/lib/python3.11/site-packages (from httpx>=0.27.2->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (1.0.7)
Requirement already satisfied: importlib-metadata>=6.8.0 in ./backend/venv/lib/python3.11/site-packages (from litellm>=1.53.1->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (8.6.1)
Requirement already satisfied: jinja2<4.0.0,>=3.1.2 in ./backend/venv/lib/python3.11/site-packages (from litellm>=1.53.1->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (3.1.6)
Requirement already satisfied: jsonschema<5.0.0,>=4.22.0 in ./backend/venv/lib/python3.11/site-packages (from litellm>=1.53.1->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (4.23.0)
Requirement already satisfied: tokenizers in ./backend/venv/lib/python3.11/site-packages (from litellm>=1.53.1->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (0.21.0)
Requirement already satisfied: mdurl~=0.1 in ./backend/venv/lib/python3.11/site-packages (from markdown-it-py>=2.2.0->rich->-r requirements.txt (line 32)) (0.1.2)
Requirement already satisfied: joblib in ./backend/venv/lib/python3.11/site-packages (from nltk>=3.9.1->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (1.4.2)
Requirement already satisfied: cryptography<45,>=41.0.5 in ./backend/venv/lib/python3.11/site-packages (from pyOpenSSL>=24.3.0->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (44.0.2)
Requirement already satisfied: fake-http-header<0.4.0,>=0.3.5 in ./backend/venv/lib/python3.11/site-packages (from tf-playwright-stealth>=1.1.0->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (0.3.5)
Requirement already satisfied: cffi>=1.12 in ./backend/venv/lib/python3.11/site-packages (from cryptography<45,>=41.0.5->pyOpenSSL>=24.3.0->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (1.17.1)
Requirement already satisfied: zipp>=3.20 in ./backend/venv/lib/python3.11/site-packages (from importlib-metadata>=6.8.0->litellm>=1.53.1->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (3.21.0)
Requirement already satisfied: MarkupSafe>=2.0 in ./backend/venv/lib/python3.11/site-packages (from jinja2<4.0.0,>=3.1.2->litellm>=1.53.1->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (3.0.2)
Requirement already satisfied: jsonschema-specifications>=2023.03.6 in ./backend/venv/lib/python3.11/site-packages (from jsonschema<5.0.0,>=4.22.0->litellm>=1.53.1->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (2024.10.1)
Requirement already satisfied: referencing>=0.28.4 in ./backend/venv/lib/python3.11/site-packages (from jsonschema<5.0.0,>=4.22.0->litellm>=1.53.1->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (0.36.2)
Requirement already satisfied: rpds-py>=0.7.1 in ./backend/venv/lib/python3.11/site-packages (from jsonschema<5.0.0,>=4.22.0->litellm>=1.53.1->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (0.23.1)
Requirement already satisfied: huggingface-hub<1.0,>=0.16.4 in ./backend/venv/lib/python3.11/site-packages (from tokenizers->litellm>=1.53.1->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (0.29.2)
Requirement already satisfied: pycparser in ./backend/venv/lib/python3.11/site-packages (from cffi>=1.12->cryptography<45,>=41.0.5->pyOpenSSL>=24.3.0->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (2.22)
Requirement already satisfied: filelock in ./backend/venv/lib/python3.11/site-packages (from huggingface-hub<1.0,>=0.16.4->tokenizers->litellm>=1.53.1->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (3.17.0)
Requirement already satisfied: fsspec>=2023.5.0 in ./backend/venv/lib/python3.11/site-packages (from huggingface-hub<1.0,>=0.16.4->tokenizers->litellm>=1.53.1->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (2025.3.0)
Requirement already satisfied: packaging>=20.9 in ./backend/venv/lib/python3.11/site-packages (from huggingface-hub<1.0,>=0.16.4->tokenizers->litellm>=1.53.1->Crawl4AI>=0.4.248->-r requirements.txt (line 16)) (24.2)
Starting backend server...

## Reverting to Separate Frontend/Backend

If you want to revert to using separate containers:

1. Edit docker-compose.yml and uncomment the frontend service
2. Run:
   Debug: Command is 'docker-down', remaining args: ''
Stopping Docker services...
Docker services stopped!
Debug: Command is 'docker-up', remaining args: ''
Starting Docker services...
Exporting environment variables from .env file...
Docker services started!
You can check the status with: ./manage.sh check
