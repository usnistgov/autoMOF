import serial
import time


class ModularUniversalActuator:
    def __init__(self, port='COM6', baudrate=9600):
        try:
            # Initialize serial connection
            # The manual specifies RS-232/RS-485 DB9 communication [1]
            self.ser = serial.Serial(
                port=port, 
                baudrate=baudrate, 
                timeout=1, 
                write_timeout=1
            )
            time.sleep(2) # Wait for connection to stabilize
            print(f"Connected to Actuator on {port}")
        except serial.SerialException as e:
            print(f"Connection Error: {e}")
            exit(1)

    def send_command(self, cmd):
        """
        Sends a command to the actuator. 
        The manual indicates commands are followed by <enter> [1].
        """
        # Using \r\n as the standard for <enter>
        full_cmd = (cmd + '\r\n').encode('utf-8')
        self.ser.write(full_cmd)
        
        # Read the response from the actuator
        response = self.ser.readline().decode('utf-8').strip()
        return response

    # --- Two Position Mode Commands ---

    def move_to_b(self):
        """Sends actuator from Position A to Position B [1].""" #Alicat(CO2+N2) in
        print("Moving to Position B...")
        return self.send_command("CC") 

    def move_to_a(self):
        """Sends actuator from Position B to Position A [1].""" #MKS(N2) in 
        print("Moving to Position A...")
        return self.send_command("CW")

    def toggle_position(self):
        """Toggles actuator to the opposite position [1]."""
        print("Toggling position...")
        return self.send_command("TO")

    # --- Status Commands ---

    def get_current_position(self):
        """Displays the current position ('A' or 'B') [1]."""
        return self.send_command("CP") #Returns as CPA or CPB 

    def get_status(self):
        """Returns CP (position), AM (mode), NP (ports), and SO (offset) [1]."""
        return self.send_command("STAT")

    def close(self):
        self.ser.close()




# ==========================================
# Example Usage
# ==========================================
#if __name__ == "__main__":
    # Replace 'COM5' with your actual port
    #actuator = ModularUniversalActuator(port='COM5')

   # try:
        # 1. Check where the valve is currently
        #pos = actuator.get_current_position()
       # print(f"Current Position: {pos}")

        # 2. Move to Position B
        #actuator.move_to_b()
       # time.sleep(2) # Give the motor time to move

        # 3. Toggle back to A
       # actuator.toggle_position()
       # time.sleep(2)

        # 4. Final status check
       # print(f"Final Status: {actuator.get_status()}")

   # except KeyboardInterrupt:
       # print("\nStopped by user")
    #finally:
       # actuator.close()
       # print("Connection closed.")