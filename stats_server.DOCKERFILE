# Use the NVIDIA GPU Cloud base image
FROM nvcr.io/nvidia/cuda:12.2.2-base-ubuntu22.04

# Install Python and other dependencies
RUN apt-get update && apt-get install -y python3 python3-pip

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set the environment variable for Flask
ENV FLASK_APP=stats_server.py

# Expose the port the app will run on
EXPOSE 5050

# Start the Flask app
CMD ["flask", "run", "--host=0.0.0.0"]
