import serial
import time

from alicat_driver import AlicatController
mfc = AlicatController(port='COM5')

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

    # --- Individual Functions ---
    def set_valve_1(self, open_valve=True):
        """Set Valve 1: True for Open, False for Closed"""
        cmd = 'A' if open_valve else 'a'
        state = "Open" if open_valve else "Closed"
        self._send(cmd, f"Setting Valve 1 to {state}")

    def set_valve_2(self, open_valve=True):
        """Set Valve 2: True for Open, False for Closed"""
        cmd = 'B' if open_valve else 'b'
        state = "Open" if open_valve else "Closed"
        self._send(cmd, f"Setting Valve 2 to {state}")

    def set_back_open(self):
        self._send('A', 'Valve 1 open')

    def set_back_close(self):
        self._send('a', 'Valve 1 closed')

    def set_front_vacuum(self):
        self._send('B', 'Valve 2 open')

    def set_front_gas(self):
        self._send('b', 'Valve 2 closed')

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

#ard = SolenoidController('COM8 ')
open_all = ard.open_all
close_all = ard.close_all
toggle_all = ard.toggle_all
set_valve_1 = ard.set_valve_1
set_valve_2 = ard.set_valve_2
set_back_open = ard.set_back_open
set_back_closed = ard.set_back_close
set_front_vacuum = ard.set_front_vacuum
set_front_gas = ard.set_front_gas

def vacuum_off():
    #turn off vacuum manually
    ard.set_front_gas()
    time.sleep(5)
    mfc.set_flow('pure_n2', .5)
    triggered = False
    while not triggered:
        alert = ard.check_for_alerts()
        if alert == "PRESSURE_TRIGGERED":
            print("Pressure switch triggered. Opening valve 2.")
            triggered = True
    ard.set_back_open()
    print("Valve 2 Opened")

init = mfc.__init__
set_flow = mfc.set_flow
set_press = mfc.set_press
get_flow = mfc.get_flow
close = mfc.close
send_command = mfc.send_command
