
import sys
sys.path.append("C://Users//drmxlt//Documents//Cu_BTC_synth//")

import numpy as np
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

from drmxlt_MOF.experiments import Ternary_colordemo, Cu_BTC
from drmxlt_MOF.moving_vials import Move_Sample, find_open_vial_rack_addresses
from drmxlt_MOF.moving_vials import force_Move_Vial
from drmxlt_MOF.unit_operation import Add_fluids
from drmxlt_MOF.system_db_setup import system_db
from drmxlt_MOF.op_scheduler import create_unit_ops_df, assign_reactors, define_cp_job
from drmxlt_MOF.op_launcher import launch_scheduled_ops
from north import NorthC9

c9 = NorthC9(addr="sim")
c9 = NorthC9('A',network_serial="AU06D2C0")  # instantiate a C9 controller object with C9 network address A-

c9.default_vel=20

t2=NorthC9('B',network=c9.network)
# 
# source = np.array([1,0,0])
# destination = np.array([3,0,0])
# force_Move_Vial(source, destination, c9)

example = Cu_BTC()

unit_ops_df = create_unit_ops_df(example.sample_db, True, True, False, False, False)
# print(unit_ops_df.to_string())

unit_ops_df, reactor_df = assign_reactors(unit_ops_df, 2, 2)
# print(unit_ops_df.to_string())

unit_ops_df, overall_time = define_cp_job(unit_ops_df, 2)
print(overall_time)
print(unit_ops_df)


# reactors = reactor_df["Reactor"].to_numpy()
# for r in reactors:
#     sub_df = unit_ops_df[unit_ops_df["Reactor"] == r]
#     print("sub_df = ", sub_df)
#     temperatures = reactor_df[reactor_df["Reactor"] == r]["Reactor Temperature (C)"].to_list()[0]
#     for t in temperatures:
#       sub_sub_df = sub_df[sub_df["Reactor Temperature (C)"] == t]
#       print("sub_sub_df = ",sub_sub_df)
# #     print(temperatures)

# launch_scheduled_ops(unit_ops_df, c9, t2, system_db, example)
# ops_launcher(job_list)
