import spectrochempy as scp
import pandas as pd
import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# --- CONFIGURATION ---
# Base folder where the instrument saves .spa files
WATCH_FOLDER = Path("C:/PIKE_Technologies/AutoPRO7/Spectra") 
BASE_SAVE_PATH = Path(r"V:\internal\autoMOF\autoFTIR\ftirControl\experiment_1\sample_1")
# ---------------------

#def spa_to_csv():
 #   X = scp.read_omnic("spectrochempy/20241107115423_004_4.spa")
  #  print(f"Title: {X.title}")
   # print(f"Origin: {X.origin}")
    #print(f"Description: {X.description}")

class SPAConverter(FileSystemEventHandler):
    def __init__(self, auto_clicker=None):
       super().__init__()
       self.auto_clicker = auto_clicker
       self.last_csv_created = None
       self.current_scan = 1


    def on_created(self, event):
        # 1. Detect new .spa file
        if not event.is_directory and event.src_path.lower().endswith(".spa"):
            print(f"New SPA file detected: {event.src_path}")
            
            # Extract the filename without extension for the converter
            file_name = os.path.splitext(os.path.basename(event.src_path))[0]
            if self.convert_spa_to_csv(file_name):
                self.verify_csv_created(file_name)
           

    def convert_spa_to_csv(self,file_name, output_filename=None):
        """
        Converts a Thermo SPA file to a CSV file using SpectroChemPy.
        """
        try:
            time.sleep(2)
        # 1. Read the .spa file
        # spectrochempy automatically detects the format
            source_path = WATCH_FOLDER / f"{file_name}.spa"
            dataset = scp.read_omnic(str(source_path))

            if dataset is None:
                print(f"Error: Failed to load {file_name}.spa")
                return False
        # 2. Extract the X (wavenumber/wavelength) and Y (intensity) data
        # dataset.x is the axis, dataset.y is the data array
            #print(f"X shape: {dataset.x.shape}")
            #print(f"Y shape: {dataset.y.shape}")
            y_data = dataset.data.flatten()
            df = pd.DataFrame({
                'X': dataset.x.values ,
                'Y': y_data ,
            })
         # --- [SAVE LOGIC] ---
            # Create the Well folder inside your V: drive path
            if "REF" in file_name.lower():
                output_path = BASE_SAVE_PATH / f"{file_name}.csv"
                print(f"Saving Background")
            else:    
                scan_folder = BASE_SAVE_PATH / f"Scan_{self.current_scan}"
                scan_folder.mkdir(parents=True, exist_ok=True)
            # Save the CSV to the V: drive well folder
                output_path = scan_folder / f"{file_name}.csv"
            df.to_csv(output_path, index=False)
            # -------------------
        # 4. Save to CSV
            print(f"Successfully saved to {output_path}")
            return True
        
        #except Exception as e:
            #print(f"Error converting C:/PIKE_Technologies/AutoPRO7/Spectra/{file_name}.spa: {e}")
        except Exception as e:
            print(f"Error converting {file_name}: {e}")
            return False
        
    def verify_csv_created(self, file_name):
        scan_folder = BASE_SAVE_PATH / f"Scan_{self.current_scan}"
        expected_csv = f"{file_name}.csv"
        
        # Loop until the CSV file is actually visible in the folder
        while True:
            if any(f.name.lower() == expected_csv.lower() for f in scan_folder.iterdir()):
                print(f"Verification Success: {expected_csv} detected in Scan_{self.current_scan}!")
                self.last_csv_created = expected_csv
                if self.auto_clicker:
                    pass
                    #print("Triggering next measurement...")
                    #self.auto_clicker.click_meas()
                # You can now trigger your next event (e.g., autoclicker) here
                break
            
            print("CSV not found yet, retrying...")
            time.sleep(1)
        


def start_workflow(auto_clicker = None):
    BASE_SAVE_PATH.mkdir(parents=True, exist_ok=True)

    event_handler = SPAConverter(auto_clicker=auto_clicker)
    observer = Observer()
    observer.schedule(event_handler, str(WATCH_FOLDER), recursive=False)
    
    print(f"Monitoring {WATCH_FOLDER} for SPA files...")
    observer.start()
    return event_handler, observer  


