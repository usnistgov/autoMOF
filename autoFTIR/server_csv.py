import json
import time
import threading
import signal
import sys
import zmq
import csv
import os

from datetime import datetime

# Import the logic from your li850.py file
from li850 import config, get_data 

# ================= CONFIGURATION =================
FOLDER_NAME = "experiment_1/gasData"
start_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
FILENAME = f"gas data run {start_time_str}.csv"
FILE_PATH = os.path.join(FOLDER_NAME, FILENAME)
stop_event = threading.Event()

CONFIG = {
    "zmq": {
        "port": "5555", 
        "address": "tcp://*:5555", # Bind to all interfaces
    },
    "sensor": {
        "interval": 0.2 # Read every 0.2 seconds
    }
}

# ================= ZMQ PUBLISHER (Sensor Logic) =================
def sensor_publisher_thread():
    """
    Reads data from LI-850 and publishes it via ZMQ.
    """
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(CONFIG["zmq"]["address"])
    
    print("[Sensor] Configuring LI-850 instrument...")
    config() 
    
    print(f"[Sensor] ZMQ Publisher started on {CONFIG['zmq']['address']}")
    
    while not stop_event.is_set():
        data_dict = get_data() 
        
        if data_dict:
            try:
                # Map li850 labels to clean JSON keys
                payload = {
                    "temp": data_dict.get("Cell Temp"),
                    "press": data_dict.get("Cell Press"),
                    "co2": data_dict.get("CO2"),
                    "h2o": data_dict.get("H2O"),
                    "timestamp": datetime.now().isoformat()
                }
                # Send data as a JSON string
                socket.send_string(json.dumps(payload))
            except Exception as e:
                print(f"[Sensor] Payload error: {e}")

        time.sleep(CONFIG["sensor"]["interval"])
    socket.close()
    context.term()
    print("Sensor] Publisher thread stopped.")

# ================= ZMQ SUBSCRIBER (CSV Logic) =================
def storage_subscriber_thread():
    """
    Subscribes to the ZMQ stream and writes data to CSV.
    """
    if not os.path.exists(FOLDER_NAME):
        os.makedirs(FOLDER_NAME)
        print(f"[Storage] Created folder: {FOLDER_NAME}")
    
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://localhost:{CONFIG['zmq']['port']}")
    # Subscribe to all messages (empty string means everything)
    socket.setsockopt_string(zmq.SUBSCRIBE, "")
    
    print(f"[Storage] Saving data to {FILE_PATH}")

    with open(FILE_PATH, mode='a', newline='') as csv_file:
        fieldnames = ["timestamp", "temp", "press", "co2", "h2o"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        
        # Write header because each file is a new run
        writer.writeheader()

        while not stop_event.is_set():
            try:
                message = socket.recv_string()
                payload = json.loads(message)
                writer.writerow(payload)
                csv_file.flush() 
            except zmq.Again:
                pass
            except Exception as e:
                print(f"[Storage] Error: {e}")

        socket.close()
        context.term()
        print("[Storage] Subscriber thread stopped.")

def start_server():
    """Function to start the publisher and subscriber threads."""
    pub_thread = threading.Thread(target=sensor_publisher_thread, daemon=True)
    pub_thread.start()

    sub_thread = threading.Thread(target=storage_subscriber_thread, daemon=True)
    sub_thread.start()
    print("ZMQ CSV Server is running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)

def stop_server():
    """Signals the threads to stop and clean up."""
    print("Stopping ZMQ CSV Server...")
    stop_event.set()


# if __name__ == "__main__":
#     start_server()
#     print("ZMQ CSV Server is running. Press Ctrl+C to stop.")
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("\nShutting down...")
#         sys.exit(0)