FROM python:3.12-slim

# Prevent Python from writing bytecode and buffer stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies (e.g. ffmpeg for audio handling)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency requirements and package configuration
COPY pyproject.toml requirements.txt ./

# Install python dependencies and project package
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -e .

# Copy application source code
COPY . .

# Ensure directory for persistent SQLite data volume exists
RUN mkdir -p /data

# Default command to run the Telegram bot
CMD ["python", "-m", "app.main"]
