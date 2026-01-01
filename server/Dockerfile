FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY api.py .
COPY schema.sql .

# Copy static files (Web App + Admin Panel)
COPY static/ ./static/

# Create init script for database
COPY schema.sql /docker-entrypoint-initdb.d/init.sql

# Run
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
