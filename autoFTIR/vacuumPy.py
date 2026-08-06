import serial
import time

from alicat_driver import AlicatController
mfc = AlicatController(port='COM5')

# Driver that communicates with arduino board. Sends a string of an uppercase or lowercase letter which corresponds to a command in the arduino vacuumControl.ino script. 
# Most important commands are set_back_open through set_front_gas.
# monitor_and_open_valve() works with alicats to detect a pressure threshold and open the back valve when that threshold is reached.

class SolenoidController:
    def __init__(self, port='COM8', baudrate=9600):
        try:
            self.arduino = serial.Serial(port=port, baudrate=baudrate, timeout=1)
            time.sleep(2) 
            print(f"Connected to Arduino on {port}")
        except serial.SerialException as e:
            print(f"Connection Error: {e}")
            self.arduino = None

    # --- Synchronized Functions ---
    def open_all(self):
        self._send('1', "Opening all valves")

    def close_all(self):
        self._send('0', "Closing all valves")

    def toggle_all(self):
        self._send('T', "Toggling all valves")

    # # --- Individual Functions ---
    # def set_valve_1(self, open_valve=True):
    #     """Set Valve 1: True for Open, False for Closed"""
    #     cmd = 'A' if open_valve else 'a'
    #     state = "Open" if open_valve else "Closed"
    #     self._send(cmd, f"Setting Valve 1 to {state}")

    # def set_valve_2(self, open_valve=True):
    #     """Set Valve 2: True for Open, False for Closed"""
    #     cmd = 'B' if open_valve else 'b'
    #     state = "Open" if open_valve else "Closed"
    #     self._send(cmd, f"Setting Valve 2 to {state}")

    # toggle output valve between open and closed

    def set_back_open(self):
        self._send('A', 'Output valve open')

    def set_back_closed(self):
        self._send('a', 'Output valve closed')

    # toggle input valve between vacuum and gas line

    def set_front_vacuum(self):
        self._send('B', 'Input valve set to vacuum')

    def set_front_gas(self):
        self._send('b', 'Input valve set to gas')

    # --- Utility Functions ---
    def check_for_alerts(self):
        if self.arduino and self.arduino.in_waiting > 0:
            alert = self.arduino.readline().decode('utf-8').strip()
            print(f"[SYSTEM ALERT] {alert}")
            return alert
        return None

    def _send(self, char, description):
        if self.arduino:
            print(description)
            self.arduino.write(char.encode())
            response = self.arduino.readline().decode('utf-8').strip()
            if response:
                print(f"Arduino: {response}")

    def disconnect(self):
        if self.arduino:
            self.arduino.close()
            print("Connection closed.")

ard = SolenoidController(port='COM8')

# commands to control from this script, comment out if you want to control from ftir_control.py
open_all = ard.open_all
close_all = ard.close_all
toggle_all = ard.toggle_all
#set_valve_1 = ard.set_valve_1
#set_valve_2 = ard.set_valve_2
set_back_open = ard.set_back_open
set_back_closed = ard.set_back_closed
set_front_vacuum = ard.set_front_vacuum
set_front_gas = ard.set_front_gas

# gas name ex: 'n2', 'co2', 'pure_n2'

def monitor_and_open_valve(gas_name, pressure_threshold=17.0):
    print(f"Monitoring {gas_name} pressure. Valve will open at {pressure_threshold} psi...")
    
    try:
        while True:
            # Read the current pressure from the MFC
            current_pressure = mfc.get_press(gas_name)
            
            if current_pressure is not None:
                #print(f"Current Pressure: {current_pressure} psi")
                
                if current_pressure >= pressure_threshold:
                    print(f"Pressure reached {pressure_threshold} psi. Opening back valve...")
                    ard.set_back_open()
                    break # Exit loop after opening the valve
            else:
                print("Failed to read pressure. Retrying...")

            #time.sleep(1) # Check every second to avoid flooding the serial port
            
    except KeyboardInterrupt:
        print("Monitoring stopped by user.")
    
def vacuum_on():
    #turn on vacuum manually
    ard.set_front_vacuum()
    ard.set_back_closed()

def vacuum_off(flowrate = .1, pressure_threshold = 17):
    #turn off vacuum manually
    ard.set_front_gas()
    time.sleep(5)
    mfc.set_flow('pure_n2', flowrate)
    monitor_and_open_valve('pure_n2', pressure_threshold)
    
#alicat commands to control from this script, comment out if you want to control from ftir_control.py
init = mfc.__init__
set_flow = mfc.set_flow
#set_press = mfc.set_press
get_flow = mfc.get_flow
close = mfc.close
send_command = mfc.send_command



