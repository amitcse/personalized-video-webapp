# Use the official Playwright Python image with browsers baked in
FROM mcr.microsoft.com/playwright/python:v1.51.0-noble


# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install ffmpeg for audio/video processing
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy application source code
COPY . ./

# Ensure Playwright browsers are installed
RUN playwright install --with-deps

# Create directories for generated files
RUN mkdir -p static/videos output

# Expose application port
EXPOSE 8000

# Start the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
