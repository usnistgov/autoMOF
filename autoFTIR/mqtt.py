import json
import signal
import sys
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# ================= CONFIGURATION =================
CONFIG = {
    "mqtt": {
        "broker": "localhost",
        "port": 1883,
        "topic": "lab/gas_analyzer/data",
    },
    "influx": {
        "url": "http://localhost:8086",
        "token": "YOUR_INFLUX_TOKEN",
        "org": "your_org",
        "bucket": "gas_data",
    }
}

# Initialize InfluxDB Client
influx_client = InfluxDBClient(url=CONFIG["influx"]["url"], token=CONFIG["influx"]["token"], org=CONFIG["influx"]["org"])
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

# ================= MQTT CALLBACKS =================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected! Listening on {CONFIG['mqtt']['topic']}...")
        client.subscribe(CONFIG["mqtt"]["topic"])
    else:
        print(f"Connection failed: {rc}")

def on_message(client, userdata, msg):
    try:
        # 1. Parse the incoming data
        payload = json.loads(msg.payload.decode())
        
        # 2. Build the data point
        point = Point("gas_readings") \
            .field("temperature", float(payload['temp'])) \
            .field("co2", float(payload['co2'])) \
            .field("h2o", float(payload['h2o'])) \
            .field("pressure", float(payload['press'])) \
            .time(time.time_ns(), WritePrecision.NS)
        
        # 3. Write directly to DB (fast enough for 5Hz)
        write_api.write(bucket=CONFIG["influx"]["bucket"], record=point)
        print(f"Stored: CO2={payload['co2']} | Temp={payload['temp']}")
        
    except Exception as e:
        print(f"Error processing message: {e}")

# ================= MAIN =================
def signal_handler(sig, frame):
    print("\nStopping...")
    sys.exit(0)

if __name__ == "__main__":
    import time
    signal.signal(signal.SIGINT, signal_handler)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(CONFIG["mqtt"]["broker"], CONFIG["mqtt"]["port"], 60)
    
    # loop_forever() is simpler for apps that only do one thing
    client.loop_forever() 