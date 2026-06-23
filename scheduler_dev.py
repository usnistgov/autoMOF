import sys
# sys.path.append("C://Users//asm6//drmxlt//drmxlt//")
sys.path.append("C://Users//drmxlt//Documents//Cu_BTC_synth_control_test//")

import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

import numpy as np


from drmxlt_MOF.op_scheduler import create_unit_ops_df
from drmxlt_MOF.experiments import Ternary_colordemo, Cu_BTC


example = Cu_BTC()

num_reactors = 1


unit_ops_df = create_unit_ops_df(example.sample_db, 
                                 True, # Add fluids
                                 True, # React
                                 6, # Wash_Cycles
                                 True, # Dry
                                 False, # Independent Centrifuge step
                                 False, # Independent Remove_supernatent step
                                 False, # Independent Sonicate step
                                 )


print(unit_ops_df)