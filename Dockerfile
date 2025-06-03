FROM python:3.12

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install watchdog for auto-reload
RUN pip install watchdog

# Copy project files
COPY . /app

# Expose logs to console
ENV PYTHONUNBUFFERED=1

# Run with watchdog to auto-reload on changes (optional for dev)
CMD ["watchmedo", "auto-restart", "--directory=.", "--pattern=*.py", "--recursive", "--", "python", "bot.py"]
