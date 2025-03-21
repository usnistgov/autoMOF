import sys
import os

sys.path.append(r".\\drmxlt_MOF\\")

import numpy as np

from drmxlt_MOF.experiments import Ternary_colordemo
from drmxlt_MOF.system_db_setup import system_db
from drmxlt_MOF.unit_operation import Add_fluids



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
#TODO update system db for vial position as it's being moved around
#TODO find an open spot on the vial rack to put the vial
    
print(example.sample_db)
print("\n")
print(example.fluid_db)
print("\n")
print(system_db)

