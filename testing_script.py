# import sys
import os

import sys
sys.path.append("C://Users//drmxlt//Documents//Cu_BTC_synth//")

import numpy as np

from drmxlt_MOF.experiments import Ternary_colordemo, Cu_BTC
from drmxlt_MOF.system_db_setup import system_db
from drmxlt_MOF.unit_operation import Add_fluids, Preheat_reactor, Start_reaction
from drmxlt_MOF.moving_vials import Move_Sample, find_open_vial_rack_addresses

from north import NorthC9

# c9 = NorthC9(addr="sim")
c9 = NorthC9('A',network_serial="AU06D2C0")  # instantiate a C9 controller object with C9 network address A-
t2=NorthC9('B',network=c9.network)

c9.default_vel=20

# from drmxlt_MOF.dummy_c9 import dummy_c9
# 
# c9 = dummy_c9()

# example = Ternary_colordemo()
example = Cu_BTC()
#TODO: push databases to Cordra

# print(example.sample_db)
# print("\n")
# print(example.fluid_db)

# print(system_db)

list_of_samples = []
for key in example.sample_db.keys():
    list_of_samples.append(example.sample_db[key]["Sample ID"])

# print(list_of_samples[0])
for i, sample in enumerate(list_of_samples[0:2]):
    print(sample)
    Add_fluids(sample, c9, system_db, example)
    
    possible_destinations = find_open_vial_rack_addresses(system_db)
    destination = possible_destinations[0,:]
    Move_Sample(sample, destination, example.sample_db, system_db, c9)
    
    reactor_zip = np.array([4,0,i])
    Preheat_reactor(sample, reactor_zip, c9, t2, system_db, example)
    
    Start_reaction(sample, reactor_zip, c9, t2, system_db, example)
    
    
    
    

# Add_fluids(list_of_samples[0], c9, system_db, example)
# 
# open_vial_positions = find_open_vial_rack_addresses(system_db)
# print("checking open positions at the end of Add_fluids")
# print(open_vial_positions)
# 
# possible_destinations = find_open_vial_rack_addresses(system_db)
# destination = possible_destinations[0,:]
# Move_Sample(list_of_samples[0], destination, example.sample_db, system_db, c9)
# 
# open_vial_positions = find_open_vial_rack_addresses(system_db)
# print("checking open positions after moving back to the rack")
# print(open_vial_positions)

    
print(example.sample_db)
print("\n")
print(example.fluid_db)
print("\n")
print(system_db)

