# AI-Scraper

AI-Scraper is a web application that generates web scraping scripts automatically using AI. Users input a URL and the data fields they want, and the system outputs a working Python script or runs it in isolated cloud containers for safe execution.

## Features

- **AI-Powered Script Generation**: Automatically generates Python web scraping scripts using AI
- **Multiple Output Formats**: Download scripts or run them in the cloud for CSV/JSON output
- **Containerized Execution**: Safe, isolated script execution in Docker containers using run_scraper.py
- **Scraper Runner Service**: Dedicated service for executing generated scraping scripts
- **Security-First**: Scripts run in isolated containers with timeout and resource limits
- **Real-time Monitoring**: Execution tracking with status updates and error handling
- **User Management**: Authentication and user dashboard
- **Modern Stack**: FastAPI + React with PostgreSQL database

## Architecture

- **Backend**: Python + FastAPI
- **Frontend**: React with TypeScript
- **Database**: PostgreSQL (SQLite for local development)
- **AI Integration**: OpenAI GPT / Local LLM support
- **Scraper Runner**: Dedicated service (`run_scraper.py`) for isolated script execution
- **Deployment**: Docker containers for easy deployment
- **Containerization**: Multi-service orchestration with Docker Compose

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.9+
- Node.js 16+
- PostgreSQL (or use SQLite for development)

### Development Setup

1. Clone the repository
2. Set up environment variables
3. Start the development servers

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Database
docker-compose up db
```

### Production Deployment

```bash
docker-compose up --build
```

## Scraper Runner System

### Overview
The scraper runner system provides secure, isolated execution of generated scraping scripts. The `run_scraper.py` service ensures that scripts run in controlled environments without affecting the main application.

### Key Features of run_scraper.py:
- **Container Isolation**: Scripts execute in separate Docker containers
- **Timeout Protection**: 5-minute execution timeout with graceful failure handling
- **Resource Management**: Memory and CPU limits for script execution
- **Output Handling**: Supports JSON, CSV, and XML output formats
- **Error Handling**: Comprehensive error reporting and logging
- **Security**: Scripts run with restricted permissions and no system access

### Execution Workflow:
1. User generates or uploads a scraping script via the web interface
2. Backend API queues the execution request
3. run_scraper.py receives execution instructions
4. Script is executed in an isolated container with controlled environment
5. Output is captured and stored for user download
6. Execution status and logs are returned to the user interface

### Monitoring & Logging:
- Real-time execution status updates
- Comprehensive logging for troubleshooting
- Execution time tracking and performance metrics
- Error reporting with detailed stack traces

## API Endpoints

### Authentication (`/api/auth/`)
- `POST /register` - User registration
- `POST /login` - User authentication
- `POST /refresh` - Token refresh
- `GET /me` - Get current user profile

### Scraper Management (`/api/scrapers/`)
- `GET /` - List user's scrapers
- `POST /` - Create new scraper
- `GET /{id}` - Get scraper details
- `PUT /{id}` - Update scraper
- `DELETE /{id}` - Delete scraper
- `POST /{id}/generate` - Generate AI script
- `GET /{id}/script` - Download generated script
- `POST /{id}/execute` - Execute scraper
- `GET /{id}/executions` - Get execution history

### User Management (`/api/users/`)
- `GET /profile` - Get user profile with statistics
- `PUT /profile` - Update user profile
- `GET /credits` - Get user credits
- `GET /scrapers` - Get user's scrapers
- `GET /executions` - Get user's execution history

### Admin Dashboard (`/api/admin/`)
- `GET /stats` - System statistics
- `GET /users` - List all users with filtering
- `GET /executions/recent` - Recent execution logs
- `GET /ai-logs/recent` - AI generation history
- `GET /system/health` - System health check

## Development Workflow

1. **Generate Script**: User provides URL and desired fields
2. **AI Processing**: Backend generates Python scraping script
3. **Security Validation**: Script is validated for safety
4. **Execution Queue**: Script is queued for containerized execution
5. **Container Execution**: run_scraper.py executes script in isolated environment
6. **Result Handling**: Output is processed and stored
7. **User Notification**: Results are available for download or view

## Project Structure

```
AI-Scraper/
├── backend/                    # FastAPI Backend Application
│   ├── app/
│   │   ├── main.py            # Application entry point
│   │   ├── api/               # API routes (auth, scrapers, users, admin)
│   │   ├── models.py          # Database models
│   │   ├── ai_agent.py        # AI script generation
│   │   └── database.py        # Database configuration
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Backend container
│
├── frontend/                   # React Frontend Application
│   ├── src/
│   │   ├── App.tsx           # Main application component
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Application pages
│   │   └── stores/           # State management (Zustand)
│   ├── package.json          # Node.js dependencies
│   └── Dockerfile           # Frontend container
│
├── scraper-runner/            # Script Execution Service
│   ├── run_scraper.py       # Main execution service with container isolation
│   ├── scrape-requirements.txt # Python dependencies for scraping
│   └── Dockerfile          # Runner container
│
├── docker-compose.yml         # Full stack orchestration
├── README.md                 # Project documentation
└── LICENSE                  # MIT License
```

## Configuration

### Environment Variables
Configure the following in `backend/.env`:

```bash
# AI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_scraper

# Security
SECRET_KEY=your_secret_key_here

# Script Execution
SCRIPT_TIMEOUT=300
MAX_SCRIPT_SIZE=10000
```

### Scraper Runner Dependencies
The scraper runner includes specialized dependencies for web scraping:

```
requests==2.31.0
beautifulsoup4==4.12.2
selenium==4.15.2
lxml==4.9.3
pandas==2.1.4
urllib3==2.0.7
```

## License

MIT License