# Use official lightweight Python 3.12 image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Install system dependencies for OpenCV and Pillow image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy dependency definition and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy complete application source code
COPY . .

# Expose standard Google Cloud Run port
EXPOSE 8080

# Run with production Gunicorn WSGI server optimized for Cloud Run
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 120 app:app
