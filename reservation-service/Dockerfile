FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=app/__init__.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Copy test files
COPY tests/ /app/tests/

# Run tests during build (optional, can be commented out for production)
RUN pytest

# Default command
CMD ["flask", "run", "--host=0.0.0.0"]