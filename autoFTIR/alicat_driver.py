import serial
import time

device_dict = {'co2': 'A', 'water': 'B', 'n2': 'C', 'pure_n2': 'D'}

class AlicatController:
    def __init__(self, port, baudrate=19200, timeout=1):
        """
        Initialize connection to Alicat MFCs via BB9 Hub.
        Default Alicat baudrate is typically 19200.
        """
        self.ser = serial.Serial(
            port=port, 
            baudrate=baudrate, 
            bytesize=serial.EIGHTBITS, 
            parity=serial.PARITY_NONE, 
            stopbits=serial.STOPBITS_ONE, 
            timeout=timeout
        )

    def send_command(self, command):
        """Sends a command and returns the decoded response."""
        full_command = (command + '\r').encode('ascii')
        self.ser.write(full_command)
        
        # Read response until newline
        response = self.ser.readline().decode('ascii').strip()
        return response

    def set_flow(self, gas_name, flow_rate):
        """
        Sets the flow rate for a specific device.
        device_id: 'A', 'B', etc. (or 'all' if supported by config)
        flow_rate: The value to set
        """
    
        device_id=device_dict.get(gas_name.lower())

        if device_id:
          # Command format: <ID>S<Value> (e.g., 'AS10.5')
            cmd = f"{device_id}S{flow_rate}"
            print(f"[{gas_name.upper()}] Mass Flow set to: {flow_rate}")
            return self.send_command(cmd)
        else: 
            return "Error: Gas name not found in dictionary"
    
    def set_press(self, gas_name, pressure):
        device_id=device_dict.get(gas_name.lower())

        if device_id:
            cmd = f"{device_id}P{pressure}"
            print(f"[{gas_name.upper()}] Pressure set to : {pressure}")
            return self.send_command(cmd)
        else:
            return "Error: Gas name not found in dictionary"

    def get_flow(self, gas_name):
        """Reads the current flow rate from a specific device."""
        # Command format: <ID>R
        device_id=device_dict.get(gas_name.lower())

        if device_id:
            cmd = f"{device_id}"
            response = self.send_command(cmd)
            #print(f"DEBUG: Raw response: {response}")
        
        # Alicat usually returns a comma-separated string: "Flow, Setpoint, ..."
            try:
                parts = response.split()
                if len(parts) >= 5:
                    mass_flow = float(parts[4])
                    print(f"[{gas_name.upper()}] Current Mass Flow: {mass_flow}")
                    return mass_flow
                #flow_value = response.split(',')[0]
               #return float(response.split()[0])
                else:
                    print("DEBUG: Response too short to parse")
                    return None
            except (ValueError, IndexError) as e:
                print(f"DEBUG: Parsing failed due to: {e}") # Add this line
                return None
        else:
            return "Error: Gas name not found in dictionary"

    def close(self):
        self.ser.close()

#mfc = AlicatController(port= 'COM5')






