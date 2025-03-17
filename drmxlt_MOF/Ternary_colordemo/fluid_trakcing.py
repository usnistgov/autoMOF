

# Fluids could either be in one of the vials, or one of the syringe pumps

fluid_db = {}

fluid_db["Contrast 1"] = {"Fluid Name": "Almond Milk 1",
                        "Volume (mL)": 10,
                        "Address": [1, 1, 4], # Vial rack, right rack, position 4
                        "Purged": True, #Vial rack gets pipette tips, Does not need purge
                        "Purg Vol.": 0, #Vial rack gets pipette tips, Does not need purge
                        "Empty threshold": 1 # mL
                          }


fluid_db["Contrast 2"] = {"Fluid Name": "Almond Milk 2",
                        "Volume (mL)": 10,
                        "Address": [1, 1, 5], # Vial rack, right rack, position 5
                        "Purged": True, #Vial rack gets pipette tips, Does not need purge
                        "Purg Vol.": 0, #Vial rack gets pipette tips, Does not need purge
                        "Empty threshold": 1 # mL
                          }

fluid_db["Precursor 1"] = {"Fluid Name": "Precursor 1",
                        "Volume (mL)": 300,
                        "Address": [5, 1, 0], # Syringe Pump, Pump index 1, splitter valve position 0
                        "Purged": False,
                        "Purg Vol.": 10,
                        "Empty threshold": 10 # mL
                          }


fluid_db["Precursor 2"] = {"Fluid Name": "Precursor 2",
                        "Volume (mL)": 300,
                        "Address": [5, 2, 0], # Syringe Pump, Pump index 2, splitter valve position 0
                        "Purged": False,
                        "Purg Vol.": 10,
                        "Empty threshold": 10 # mL
                          }

fluid_db["Precursor 3"] = {"Fluid Name": "Precursor 3",
                        "Volume (mL)": 300,
                        "Address": [5, 3, 0], # Syringe Pump, Pump index 1, splitter valve position 0
                        "Purged": False,
                        "Purg Vol.": 10,
                        "Empty threshold": 10 # mL
                          }

fluid_db["Solvent 1"] = {"Fluid Name": "Solvent 1",
                        "Volume (mL)": 300,
                        "Address": [5, 4, 0], # Syringe Pump, Pump index 3, splitter valve position 0
                        "Purged": False,
                        "Purg Vol.": 10,
                        "Empty threshold": 10 # mL
                          }

#TODO
# Test fluid db for:
## vials were loaded, but unassigned before?
## If at a syringe pump,
### Not pump index 0 - reserved for arm
### if splitter valve index != 0
#### Splitter valve installed on that pump?




