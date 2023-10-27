import cv2
import numpy as np
from flask import Flask, Response, request, jsonify
import threading
from ultralytics import YOLO
import time
import datetime

app = Flask(__name__)
current_frame = None
frame_count_client = 0
frame_count_server = 0
model = YOLO("yolov5s.pt")

# Specify the desired dimensions for the resized frames
RESIZED_WIDTH = 1200
RESIZED_HEIGHT = 800

@app.route('/')
def home():
    return "Welcome to Video Streaming Server!!!"

@app.route('/video_feed', methods=['POST', 'GET'])
def video_feed():
    global current_frame, frame_count_client, frame_count_server
    if request.method == 'POST':
        frame_data = request.data
        frame = np.frombuffer(frame_data, np.uint8)
        img = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        frame_width = int(request.headers['Frame-Width'])
        frame_height = int(request.headers['Frame-Height'])

        client_timestamp = float(request.headers['Client-Timestamp'])
        server_to_client_delay = time.time() - client_timestamp

        img = cv2.resize(img, (RESIZED_WIDTH, RESIZED_HEIGHT))

        start_time = time.time()
        #Inference
        results = model.predict(img)
        end_time = time.time()
        processing_delay = end_time - start_time
        #print(processing_delay)

        # current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        # print('Frame received by server at:', current_time)

        for result in results:
            for obj in result.boxes:
                x1, y1, x2, y2 = map(int, obj.xyxy[0])
                label = result.names[int(obj.cls[0])]
                confidence = obj.conf[0]

                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(img, f'{label}: {confidence:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        ret, buffer = cv2.imencode('.jpg', img)
        current_frame = buffer.tobytes()
        frame_count_client += 1
        frame_count_server += 1
       # print("Received frame from client. Total frames received:", frame_count_client)
       # print("Total frames processed:", frame_count_server)

        server_timestamp = time.time()
        server_to_browser_delay = server_timestamp - client_timestamp
        #print('Delay time (server to browser URL):', server_to_browser_delay)

        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        #print('Frame sent to browser at:', current_time)

        # Create a dictionary with the print statements as headers
        response_headers = {
            'one way delay (client to server):': str(server_to_client_delay),
            'Processing-Delay': str(processing_delay),
            # 'Frame-Received-Time': current_time,
            'Total-Frames-Received': str(frame_count_client),
            'Total-Frames-Processed': str(frame_count_server),
            'Server-to-Browser-Delay': str(server_to_browser_delay),
            # 'Frame-Sent-Time': current_time,
        }

        # Convert the dictionary to a JSON response
        response = jsonify(success=True, data="Video frame received.", **response_headers)
        response.status_code = 200

        return response
    else:
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate():
    global current_frame
    while True:
        if current_frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + current_frame + b'\r\n')

def process_frame():
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == '__main__':
    threading.Thread(target=process_frame).start()
    app.run(host='127.0.0.1', port=8080)
