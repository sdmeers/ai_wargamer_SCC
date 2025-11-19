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

# Expose the port (using 8080 is common for Cloud Run)
EXPOSE 8080

# Streamlit command to run the app. Use 8080 to match the expose and convention.
CMD ["streamlit", "run", "web_app.py", "--server.port=8080", "--server.address=0.0.0.0"]