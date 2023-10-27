# Base image
FROM ubuntu:latest

# Set the working directory in the container
WORKDIR /app

RUN apt update && apt install python3-pip -y && apt install ffmpeg -y

# Copy the requirements file
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code and yolo model into the container 
COPY yolov5su.pt .
COPY server.py .

# Start the server
CMD ["python3", "server.py"]
