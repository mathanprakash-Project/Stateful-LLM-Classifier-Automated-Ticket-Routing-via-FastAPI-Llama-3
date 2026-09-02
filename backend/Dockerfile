FROM ghcr.io/astral-sh/uv:latest AS uv_bin
FROM python:3.11-slim

# Copy uv executable from official uv image
COPY --from=uv_bin /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Optimize python behavior
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    OLLAMA_BASE_URL=http://host.docker.internal:11434

# Install build tools & dependencies with uv
COPY requirements.txt pyproject.toml ./
RUN uv pip install --system -r requirements.txt

# Copy application source code and .env
COPY app/ ./app/
COPY .env* ./

# Expose API port
EXPOSE 8000

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
