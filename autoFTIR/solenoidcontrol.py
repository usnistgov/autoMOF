import serial
import time
from serial.tools import list_ports
list = list_ports.comports()
connected = []
for element in list:
    connected.append(element.device)
    print("Connected COM ports: " + str(connected))

arduino = serial.Serial(port='COM7',   baudrate=115200, timeout=.1)
print("test2")

def write_read(x):
    arduino.write(bytes(x, 'utf-8'))
    time.sleep(0.05)
    data = arduino.readline()
    return   data



def vent_open(): 
    value = write_read(str(1))
    print(value)
def vent_close():
    value = write_read(str(2))
    print(value)
def relay2_open():
    value = write_read(str(3))
    print(value)
def relay2_close():
    value = write_read(str(4))
    print (value)

   