import sys
import os

sys.path.append(r".\\drmxlt_MOF\\")

import numpy as np

from drmxlt_MOF.experiments import Ternary_colordemo
from drmxlt_MOF.system_db_setup import system_db
from drmxlt_MOF.unit_operation import Add_fluids
from drmxlt_MOF.moving_vials import Move_Sample, find_open_vial_rack_addresses



from drmxlt_MOF.dummy_c9 import dummy_c9

c9 = dummy_c9()

example = Ternary_colordemo()

# print(example.sample_db)
# print("\n")
# print(example.fluid_db)

# print(system_db)

list_of_samples = []
for key in example.sample_db.keys():
    list_of_samples.append(example.sample_db[key]["Sample ID"])

print(list_of_samples[0])
# for sample in list_of_samples:
#     Add_fluids(sample, c9, system_db, example)

Add_fluids(list_of_samples[0], c9, system_db, example)

#TODO find an open spot on the vial rack to put the vial
open_vial_positions = find_open_vial_rack_addresses(system_db)
print("checking open positions at the end of Add_fluids")
print(open_vial_positions)

destination = np.array([3, 0, 0])
Move_Sample(list_of_samples[0], destination, example.sample_db, system_db, c9)

destination = np.array([4, 0, 0])
Move_Sample(list_of_samples[0], destination, example.sample_db, system_db, c9)

possible_destinations = find_open_vial_rack_addresses(system_db)
destination = possible_destinations[0,:]
Move_Sample(list_of_samples[0], destination, example.sample_db, system_db, c9)

open_vial_positions = find_open_vial_rack_addresses(system_db)
print("checking open positions after moving back to the rack")
print(open_vial_positions)

    
print(example.sample_db)
print("\n")
print(example.fluid_db)
print("\n")
print(system_db)

