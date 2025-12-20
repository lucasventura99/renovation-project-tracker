# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
# libpq-dev is needed for building the postgres driver wrapper
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .