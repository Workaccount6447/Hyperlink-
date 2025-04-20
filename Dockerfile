FROM python:3.10-slim

WORKDIR /app

# Install Chrome dependencies
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg \
    fonts-liberation libnss3 libxss1 libasound2 libatk-bridge2.0-0 \
    libgtk-3-0 libx11-xcb1 xdg-utils && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y ./google-chrome.deb && rm google-chrome.deb

# Install Chromedriver
RUN CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "photo_adder.py"]

