# Use the official Python image as the base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Expose the port that Streamlit will run on (Cloud Run defaults to $PORT, we use 8501 inside the container)
# Note: Streamlit's default port is 8501
EXPOSE 8501

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files (web_app.py, agents.py, and the data folder)
# Ensure the agents.py, web_app.py, and the data folder are in the same directory as this Dockerfile
COPY . /app

# Streamlit command to run the app. 
# We configure Streamlit to run on 0.0.0.0 (required for Docker/Cloud Run) 
# and explicitly set the port to 8501 (which Cloud Run will map to $PORT)
CMD ["streamlit", "run", "web_app.py", "--server.port=8501", "--server.address=0.0.0.0"]