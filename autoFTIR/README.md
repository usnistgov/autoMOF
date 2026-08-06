Python drivers and unified pyton control system.
ftir_control.py is the unified python control script
When using drivers individually/unified system make sure to comment out any other instances of the used com ports in other files. This applies to uploading ot the arduino aswell. EX: mfc = AlicatController(port='COM5')
co2_step in ftir_control.py is the current workflow for the system. 
vacuumControl.ino is the code uploaded to the arduino.
server_csv.py saves gas data to .csv file
li850.py configures the gas analyzer readout
