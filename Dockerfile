# Use python:3.8-slim as the base image
FROM python:3.8-slim

# Set the working directory
WORKDIR /app

# Copy the application code
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the entry point to run the Flask application
CMD ["python", "app.py"]
