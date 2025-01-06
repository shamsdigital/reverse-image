# Use the official Python image from Docker Hub
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose the port that your app runs on (5000)
EXPOSE 5000

# Command to run the application using Gunicorn with specified options for better performance (optional)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
