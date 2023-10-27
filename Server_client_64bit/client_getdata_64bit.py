import cv2
import requests
import time
import datetime
import csv
from picamera2 import Picamera2

# Define the TiE-API server URL
#server_url = 'http://127.0.0.1:8080/video_feed'
#server_url = 'http://192.168.20.17:30030/video_feed'
server_url = 'http://192.168.20.190:8080/video_feed'

# Create a CSV file to store the data
csv_file = open('data.csv', mode='w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['RTT', 'Processing-Delay', 'Network_Delay', 'Server-to-Browser-Delay', 'Total-Frames-Processed', 'Total-Frames-Received'])

camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
camera.start()

try:
    print('Connected to Cache Server')
    while True:  # Capture images continuously
        
        image = camera.capture_array()     

        # Convert the frame to JPEG format
        _, buffer = cv2.imencode('.jpg', image)
        frame_data = buffer.tobytes()

        headers = {
            'Content-Type': 'application/octet-stream',
            'Frame-Width': str(image.shape[1]),
            'Frame-Height': str(image.shape[0]),
            'Client-Timestamp': str(time.time())
        }
        
        start_time = time.time()
        response = requests.post(server_url, data=frame_data, headers=headers)
        end_time = time.time()
        rtt = end_time - start_time

        # Parse the response JSON
        response_data = response.json()

        # Extract the information you want from the response headers
        processing_delay = float(response_data.get('Processing-Delay', '0'))
        Network_Delay = rtt - processing_delay
        server_to_browser_delay = response_data.get('Server-to-Browser-Delay', '')
        total_frames_processed = response_data.get('Total-Frames-Processed', '')
        total_frames_received = response_data.get('Total-Frames-Received', '')

        # Print and write the data to the CSV file
        print('Round Trip time (Drone-Server-Drone):', rtt)
        csv_writer.writerow([rtt, processing_delay, Network_Delay, server_to_browser_delay, total_frames_processed, total_frames_received])
        print("Network Delay (rtt-processing):", Network_Delay)
except KeyboardInterrupt:
    pass
except Exception as e:
    print("Error:", str(e))
finally:
    csv_file.close()
