FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements-db.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt -r requirements-db.txt

# Copy application code
COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Make scripts executable
RUN chmod +x *.py

# Expose ports
EXPOSE 8888 5000

# Start the server
CMD ["python", "server.py"]
