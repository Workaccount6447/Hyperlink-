FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg git && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variables via Koyeb dashboard
# ENV BOT_TOKEN=your_bot_token_here
# ENV OWNER_ID=your_owner_id_here

CMD ["python", "main.py"]
