# AI-Scraper

AI-Scraper is a web application that generates web scraping scripts automatically using AI. Users input a URL and the data fields they want, and the system outputs a working Python script or runs it in the cloud.

## Features

- **AI-Powered Script Generation**: Automatically generates Python web scraping scripts using AI
- **Multiple Output Formats**: Download scripts or run them in the cloud for CSV/JSON output
- **Containerized Execution**: Safe, isolated script execution in Docker containers
- **User Management**: Authentication and user dashboard
- **Modern Stack**: FastAPI + React with PostgreSQL database

## Architecture

- **Backend**: Python + FastAPI
- **Frontend**: React with TypeScript
- **Database**: PostgreSQL (SQLite for local development)
- **AI Integration**: OpenAI GPT / Local LLM support
- **Deployment**: Docker containers for easy deployment

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

## Project Structure

```
AI-Scraper/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── models/
│   │   ├── ai_agent.py
│   │   └── database.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── package.json
├── docker-compose.yml
├── README.md
└── LICENSE
```

## License

MIT License