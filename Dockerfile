# Use slim Python image to reduce size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    wget \
    unzip \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy bot code
COPY . /app

# Upgrade pip and install only Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port for Flask
EXPOSE 5000

# Start bot
CMD ["python", "bot.py"]
