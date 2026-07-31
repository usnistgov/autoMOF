import serial
import time
from datetime import datetime 

# Serial communication parameters
SERIAL_PARAMS = {
    'port': 'COM7',
    'baudrate': 9600,
    'bytesize': serial.EIGHTBITS,
    'parity': serial.PARITY_NONE,
    'stopbits': serial.STOPBITS_ONE,
    'timeout': 5
}

def config():
    """
    Configures the instrument to output CO2, H2O, celltemp, and cellpres.
    Sends the command but does not print the response.
    """
    # Command configures output rate and enables the four requested sensors with strip=true
    command = ("<li850><cfg><outrate>0</outrate></cfg>"
               "<rs232><co2>true</co2><flowrate>false</flowrate>"
               "<h2o>true</h2o><celltemp>true</celltemp>"
               "<cellpres>true</cellpres><ivolt>false</ivolt>"
               "<co2abs>false</co2abs><h2oabs>false</h2oabs>"
               "<h2odewpoint>false</h2odewpoint><raw>false</raw>"
               "<echo>false</echo><strip>true</strip></rs232></li850>\r\n")
    
    try:
        with serial.Serial(**SERIAL_PARAMS) as ser:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            ser.write(command.encode('utf-8'))
            ser.flush()
            time.sleep(0.5) # Give instrument time to process configuration
    except Exception as e:
        # Configuration errors are handled silently or via internal logging 
        # as per the request that only the read function should print data.
        pass

def get_data():

    """
    Requests data from the instrument, parses the response, and prints the values.
    """
    # Request data using the same format as configuration to ensure consistency
    command = ("<li850><data>?</data><rs232><strip>true</strip></rs232></li850>\r\n")
    
    try:
        with serial.Serial(**SERIAL_PARAMS) as ser:
            ser.reset_input_buffer()
            ser.write(command.encode('utf-8'))
            ser.flush()
            #print(ser)    
            # time.sleep(0.5)
            raw_reply = ser.read_until(b'\r\n')
            reply = raw_reply.decode('utf-8', errors='ignore').strip()
            
            if reply:
                # Split the space-separated values (CO2, H2O, Temp, Pres)
                values = reply.split()
                labels = ["Cell Temp", "Cell Press", "CO2", "H2O"]
                outDict = dict(zip(labels, values))
                outDict.update({"Timestamp": datetime.now().isoformat(), "Epoch": time.time()})
                # Map labels to the received values
                for label, val in zip(labels, values):
                    try:
                        print(f"{label}: {float(val):.4f}")
                    except ValueError:
                        print(f"{label}: {val}")
                return outDict
            else:
                print("No data received from instrument.")

                
    except Exception as e:
        print(f"Error reading data: {e}")



#if __name__ == "__main__":
    config()

    # Example usage: continuously read data every second
    # while True:
    #     get_data()
    #     time.sleep(1)


#import pandas as pd
#data_list = []
#for i in range(10):
        
 #   data_list.append(get_data())
  #  time.sleep(.2)  # Wait 1 second between readings
   # print(i)
   # df = pd.DataFrame(data_list)
#print(df)
# Example Usage:
#if __name__ == "__main__":
 #   configure_instrument()
  #  read_and_print_data()