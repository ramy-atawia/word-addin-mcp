# Multi-stage Dockerfile for Word Add-in MCP Backend
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY requirements-dev.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as development
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Test stage
FROM base as test
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
CMD ["pytest", "tests/", "-v", "--cov=app", "--cov-report=xml", "--cov-report=html"]

# Production stage
FROM base as production
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]