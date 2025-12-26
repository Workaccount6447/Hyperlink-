FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for FFmpeg, Pillow, psycopg2, etc.
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    unzip \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy bot files
COPY . /app

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port for Flask
EXPOSE 5000

# Start bot
CMD ["python", "bot.py"]
