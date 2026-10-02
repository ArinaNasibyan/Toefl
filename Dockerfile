FROM python:3.12-slim

# Prevent Python from writing bytecode and buffer stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=7860

# Install system dependencies (e.g. ffmpeg for audio handling)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition
COPY pyproject.toml requirements.txt ./

# Install python dependencies first to cache layer
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application source code (including README.md)
COPY . .

# Install project package
RUN pip install --no-cache-dir --no-deps -e .

# Ensure directory for SQLite database exists and has full write permissions
RUN mkdir -p /app/data /data && chmod -R 777 /app/data /data

EXPOSE 7860

# Default command to run the Telegram bot
CMD ["python", "-m", "app.main"]
