# Production Incident Response Simulator - Docker Image
FROM python:3.11-slim

WORKDIR /app

# Set UTF-8 encoding
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Validate environment on build
RUN python -c "from env import ProductionIncidentEnv; env = ProductionIncidentEnv(); print('Environment validated successfully')"

# Expose API port
EXPOSE 7860

# Run API server for OpenEnv hackathon
CMD ["python", "api_server.py"]
