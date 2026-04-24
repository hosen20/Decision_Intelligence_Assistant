# Backend Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY backend/pyproject.toml backend/requirements.txt* /app/

# Install Python dependencies
# Try uv first (fast), fallback to pip if uv fails or not available
RUN pip install --upgrade pip setuptools wheel && \
    (pip install uv && uv sync --no-dev --frozen || pip install -r requirements.txt)

# Copy application code
COPY backend/ /app/

# Create necessary directories
RUN mkdir -p /app/models /app/logs /app/shared_volume

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
