# Scraper Runner Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for scraping
COPY scraper-requirements.txt .
RUN pip install --no-cache-dir -r scraper-requirements.txt

# Copy scraper runner code
COPY . .

# Create directories
RUN mkdir -p scripts outputs logs

# Set proper permissions
RUN chmod +x run_scraper.py

# Run the scraper runner
CMD ["python", "run_scraper.py"]