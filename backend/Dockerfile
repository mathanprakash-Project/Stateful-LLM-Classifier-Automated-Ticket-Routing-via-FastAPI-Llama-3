# Use official Python lightweight image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Prevent Python from writing .pyc files & buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Default Ollama host for Docker container (points to host machine Ollama)
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and configuration
COPY app/ ./app/
COPY .env .env

# Expose port FastAPI runs on
EXPOSE 8000

# Start FastAPI server via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
