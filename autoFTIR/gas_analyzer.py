# CO2_analyzer.py
import serial
import time
import xml.etree.ElementTree as ET   # XML parser

# ----------------------------------------------------------------------
# Serial communication parameters (adjust the port as needed)
SERIAL_PARAMS = {
    'port': 'COM6',
    'baudrate': 9600,
    'bytesize': serial.EIGHTBITS,
    'parity': serial.PARITY_NONE,
    'stopbits': serial.STOPBITS_ONE,
    'timeout': 5          # give the instrument enough time to answer
}
# ----------------------------------------------------------------------


def get_co2_reading(max_attempts:int = 5, pause: float = 0.5) -> float | None:  #  <-----CO2 in umol/mol
    """
    Open the serial port, ask the LI‑850 for a CO₂ measurement,
    parse the returned XML, and return the numeric CO₂ value.

    Returns
    -------
    float | None
        The CO₂ concentration (percent‑vol) if the instrument responded
        with a readable value, otherwise ``None``.
    """
    
    command = ("<li850><cfg><outrate>1</outrate></cfg>"
               "<rs232><co2>true</co2><flowrate>false</flowrate>"
               "<h2o>false</h2o><celltemp>false</celltemp>"
               "<cellpres>false</cellpres><ivolt>false</ivolt>"
               "<co2abs>false</co2abs><h2oabs>false</h2oabs>"
               "<h2odewpoint>false</h2odewpoint><raw>false</raw>"
               "<echo>false</echo><strip>true</strip></rs232></li850>\r\n")

    try:
        ser = serial.Serial(**SERIAL_PARAMS)
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        for attempt in range(1, max_attempts +1):
            ser.reset_input_buffer()
            ser.write(command.encode('utf-8'))
            ser.flush()

            time.sleep(pause)

        # read the whole reply up to the terminating CR/LF
            raw_reply = ser.read_until(b'\r\n')
            reply = raw_reply.decode('utf-8', errors='ignore').strip()
            ser.flush()

            if not reply:
                print(f"[Attempt {attempt}] No data received.")
                continue
        
        
            try:
                return float(reply)
            except ValueError:
                pass

        # ---- parse XML ------------------------------------------------
            try:
                root = ET.fromstring(reply)
            except ET.ParseError:
                print(f"[Attempts {attempt}] Received malformed XML:{reply}")
                continue

        # CO₂ may be <co2>5.23</co2> or <co2><val>5.23</val></co2>
            co2_elem = root.find('.//co2')
            if co2_elem is None:
                #print("No <co2> element in the reply.")
                continue

        # direct text case
            if co2_elem.text and co2_elem.text.strip():
                try:
                    return float(co2_elem.text.strip())
                except ValueError:
                    pass

        # nested <val> case
            val = co2_elem.find('val')
            if val is not None and val.text:
                try:
                    return float(val.text.strip())
                except ValueError:
                    pass

            print(f"[Attempt {attempt} ] <co2> found but value not numeric: {ET.tostring(co2_elem)}")
            continue
        
        print("All attempts exhausted, no measurement obtained")
        return None

    except serial.SerialException as e:
        print(f"Serial error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    finally:
        try:
            ser.close()
        except Exception:
            pass



def get_h2o_reading(max_attempts:int = 5, pause: float = 1.0) -> float | None:  #  <-----h2o in umol/mol
    
    command = ("<li850><cfg><outrate>1</outrate></cfg>"
               "<rs232><co2>false</co2><flowrate>false</flowrate>"
               "<h2o>true</h2o><celltemp>false</celltemp>"
               "<cellpres>false</cellpres><ivolt>false</ivolt>"
               "<co2abs>false</co2abs><h2oabs>false</h2oabs>"
               "<h2odewpoint>false</h2odewpoint><raw>false</raw>"
               "<echo>false</echo><strip>true</strip></rs232></li850>\r\n")

    try:
        ser = serial.Serial(**SERIAL_PARAMS)
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        for attempt in range(1, max_attempts +1):
            ser.reset_input_buffer()
            ser.write(command.encode('utf-8'))
            ser.flush()

            time.sleep(pause)

        # read the whole reply up to the terminating CR/LF
            raw_reply = ser.read_until(b'\r\n')
            reply = raw_reply.decode('utf-8', errors='ignore').strip()
            ser.flush()

            if not reply:
                print(f"[Attempt {attempt}] No data received.")
                continue
        
        
            try:
                value = float(reply)
                return value
            except ValueError:
                pass

        # ---- parse XML ------------------------------------------------
            try:
                root = ET.fromstring(reply)
            except ET.ParseError:
                print(f"[Attempts {attempt}] Received malformed XML:{reply}")
                continue

        # CO₂ may be <co2>5.23</co2> or <co2><val>5.23</val></co2>
            h2o_elem = root.find('.//h2o')
            if h2o_elem is None:
                #print("No <co2> element in the reply.")
                continue

        # direct text case
            if h2o_elem.text and h2o_elem.text.strip():
                try:
                    return float(h2o_elem.text.strip())
                except ValueError:
                    pass

        # nested <val> case
            val = h2o_elem.find('val')
            if val is not None and val.text:
                try:
                    return float(val.text.strip())
                except ValueError:
                    pass

            print(f"[Attempt {attempt} ] <h2o> found but value not numeric: {ET.tostring(h2o_elem)}")
            continue
        
        print("All attempts exhausted, no measurement obtained")
        return None

    except serial.SerialException as e:
        print(f"Serial error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    finally:
        try:
            ser.close()
        except Exception:
            pass



def get_pressure_reading(max_attempts:int = 5, pause: float = 1.0) -> float | None:  #  <----- in kPa
    
    command = ("<li850><cfg><outrate>1</outrate></cfg>"
               "<rs232><co2>false</co2><flowrate>false</flowrate>"
               "<h2o>false</h2o><celltemp>false</celltemp>"
               "<cellpres>true</cellpres><ivolt>false</ivolt>"
               "<co2abs>false</co2abs><h2oabs>false</h2oabs>"
               "<h2odewpoint>false</h2odewpoint><raw>false</raw>"
               "<echo>false</echo><strip>true</strip></rs232></li850>\r\n")

    try:
        ser = serial.Serial(**SERIAL_PARAMS)
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        for attempt in range(1, max_attempts +1):
            ser.reset_input_buffer()
            ser.write(command.encode('utf-8'))
            ser.flush()

            time.sleep(pause)

        # read the whole reply up to the terminating CR/LF
            raw_reply = ser.read_until(b'\r\n')
            reply = raw_reply.decode('utf-8', errors='ignore').strip()
            ser.flush()

            if not reply:
                print(f"[Attempt {attempt}] No data received.")
                continue
        
        
            try:
                value = float(reply)
                return value
            except ValueError:
                pass

        # ---- parse XML ------------------------------------------------
            try:
                root = ET.fromstring(reply)
            except ET.ParseError:
                print(f"[Attempts {attempt}] Received malformed XML:{reply}")
                continue

        # CO₂ may be <co2>5.23</co2> or <co2><val>5.23</val></co2>
            pres_elem = root.find('.//cellpres')
            if pres_elem is None:
                #print("No <co2> element in the reply.")
                continue

        # direct text case
            if pres_elem.text and pres_elem.text.strip():
                try:
                    return float(pres_elem.text.strip())
                except ValueError:
                    pass

        # nested <val> case
            val = pres_elem.find('val')
            if val is not None and val.text:
                try:
                    return float(val.text.strip())
                except ValueError:
                    pass

            print(f"[Attempt {attempt} ] <cellpres> found but value not numeric: {ET.tostring(pres_elem)}")
            continue
        
        print("All attempts exhausted, no measurement obtained")
        return None

    except serial.SerialException as e:
        print(f"Serial error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    finally:
        try:
            ser.close()
        except Exception:
            pass



def get_temp_reading(max_attempts:int = 5, pause: float = 1.0) -> float | None:  #  <----- in C
    
    command = ("<li850><cfg><outrate>1</outrate></cfg>"
               "<rs232><co2>false</co2><flowrate>false</flowrate>"
               "<h2o>false</h2o><celltemp>true</celltemp>"
               "<cellpres>false</cellpres><ivolt>false</ivolt>"
               "<co2abs>false</co2abs><h2oabs>false</h2oabs>"
               "<h2odewpoint>false</h2odewpoint><raw>false</raw>"
               "<echo>false</echo><strip>true</strip></rs232></li850>\r\n")

    try:
        ser = serial.Serial(**SERIAL_PARAMS)
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        for attempt in range(1, max_attempts +1):
            ser.reset_input_buffer()
            ser.write(command.encode('utf-8'))
            ser.flush()

            time.sleep(pause)

        # read the whole reply up to the terminating CR/LF
            raw_reply = ser.read_until(b'\r\n')
            reply = raw_reply.decode('utf-8', errors='ignore').strip()
            ser.flush()

            if not reply:
                print(f"[Attempt {attempt}] No data received.")
                continue
            import pdb; pdb.set_trace()
        
            try:
                value = float(reply)
                return value
            except ValueError:
                pass

        # ---- parse XML ------------------------------------------------
            try:
                root = ET.fromstring(reply)
            except ET.ParseError:
                print(f"[Attempts {attempt}] Received malformed XML:{reply}")
                continue

        # CO₂ may be <co2>5.23</co2> or <co2><val>5.23</val></co2>
            temp_elem = root.find('.//celltemp')
            if temp_elem is None:
                #print("No <co2> element in the reply.")
                continue

        # direct text case
            if temp_elem.text and temp_elem.text.strip():
                try:
                    return float(temp_elem.text.strip())
                except ValueError:
                    pass

        # nested <val> case
            val = temp_elem.find('val')
            if val is not None and val.text:
                try:
                    return float(val.text.strip())
                except ValueError:
                    pass

            print(f"[Attempt {attempt} ] <celltemp> found but value not numeric: {ET.tostring(temp_elem)}")
            continue
        
        print("All attempts exhausted, no measurement obtained")
        return None

    except serial.SerialException as e:
        print(f"Serial error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    finally:
        try:
            ser.close()
        except Exception:
            pass



# ----------------------------------------------------------------------
#if __name__ == "__main__":
    #reading = get_co2_reading()
    #if reading is not None:
     #   print(f"CO₂ reading: {reading} umol/mol")
    #else:
     #   print("Failed to obtain a CO₂ measurement.")