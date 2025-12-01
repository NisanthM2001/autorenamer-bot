FROM python:3.10-slim

WORKDIR /app

# Install system packages including ntpdate for time sync
RUN apt-get update && apt-get install -y \
    git \
    ntpdate \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Create directories
RUN mkdir -p downloads thumbnails

# Sync system time and run bot
CMD sh -c "ntpdate -s time.nist.gov || timedatectl set-ntp true; python main.py"
