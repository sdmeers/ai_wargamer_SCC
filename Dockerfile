# Use the official Python image as the base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies (Copy only requirements first for better Docker caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- CRITICAL STEP: Copy the pre-generated intelligence data ---
# This file must exist *before* the Docker build starts.
COPY intelligence_analysis.json .

# Copy all application files (web_app.py, agents.py, and the data folder)
COPY . /app

# The Cloud Run platform sets the PORT environment variable (default 8080) 
# and requires the container to listen on it. 
# We use the variable here for maximum compatibility.
EXPOSE 8080

# Streamlit command to run the app. It reads the PORT env var automatically, 
# but explicitly setting it via the env var is best practice for CMD.
# If $PORT is not set, we default to 8080.
CMD ["streamlit", "run", "web_app.py", "--server.port", "${PORT:-8080}", "--server.address=0.0.0.0"]