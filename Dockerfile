FROM python:3.10-slim

WORKDIR /app

# Install system packages (ntpsec-ntpdate is the modern replacement for ntpdate)
RUN apt-get update && apt-get install -y \
    git \
    ntpsec \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Create directories
RUN mkdir -p downloads thumbnails

# Start: Sync time with ntpd then run bot
CMD ntpd -g -q -n && python main.py
