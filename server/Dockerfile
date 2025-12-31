FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY api.py .

# Run
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
