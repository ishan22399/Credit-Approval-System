# Use official Python runtime as base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_HOME=/app

# Set work directory
WORKDIR $APP_HOME

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate && python manage.py ingest_data && gunicorn credit_system.wsgi:application --bind 0.0.0.0:8000 --workers 4"]
