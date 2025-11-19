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
COPY data /app/data

# Copy all application files (web_app.py, agents.py, and the data folder)
COPY . /app

# The Cloud Run platform sets the PORT environment variable (default 8080) 
# and requires the container to listen on it. 
EXPOSE 8080

# --- FIX: Using the hybrid JSON/Shell form to allow variable substitution
# This uses the JSON array format (good for signal handling) but explicitly
# calls sh -c (good for resolving the ${PORT:-8080} environment variable).
CMD ["/bin/sh", "-c", "streamlit run web_app.py --server.port ${PORT:-8080} --server.address 0.0.0.0"]