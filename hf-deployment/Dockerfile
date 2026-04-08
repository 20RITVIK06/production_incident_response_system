# Production Incident Response Simulator - Gradio Interface
# This version runs the Gradio web interface on port 7860
FROM python:3.11-slim

WORKDIR /app

# Set UTF-8 encoding
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install dependencies (including gradio)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose Gradio port
EXPOSE 7860

# Validate environment on build
RUN python -c "from env import ProductionIncidentEnv; env = ProductionIncidentEnv(); print('Environment validated successfully')"

# Run Gradio app
CMD ["python", "app.py"]
