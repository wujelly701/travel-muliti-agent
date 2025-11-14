# Travel Agent MVP Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency spec first for layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/
COPY start.py ./

ENV PYTHONPATH=src \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "travel_agent.api:app", "--host", "0.0.0.0", "--port", "8000"]
