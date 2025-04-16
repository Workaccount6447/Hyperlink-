# Use an official Python 3.10 base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot's source code
COPY . .

# Expose the port (if needed)
EXPOSE 8443

# Command to run the bot
CMD ["python", "photo_adder.py"]
