
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
from drmxlt_MOF.op_scheduler import create_unit_ops_df, assign_reactors, define_cp_job, reset_schedule
from drmxlt_MOF.op_launcher import launch_scheduled_ops, execute_scheduled_ops
from north import NorthC9

c9 = NorthC9(addr="sim")
c9 = NorthC9('A',network_serial="AU06D2C0")  # instantiate a C9 controller object with C9 network address A-

c9.default_vel=15

t2=NorthC9('B',network=c9.network)
# 
# source = np.array([1,0,0])
# destination = np.array([3,0,0])
# force_Move_Vial(source, destination, c9)

example = Cu_BTC()
# print(example.sample_db)

unit_ops_df = create_unit_ops_df(example.sample_db, True, True, False, False, False)
print("Created Unit Ops DF")

unit_ops_df, reactor_df = assign_reactors(unit_ops_df, 1, 4)
print("Assigned Reactors")

unit_ops_df, overall_time = define_cp_job(unit_ops_df, 1)
print("Solved Constraint Satisfaction Problem")

# unit_ops_df.loc[0, "Status"] = "Completed"
# unit_ops_df.loc[1, "Status"] = "Completed"
# unit_ops_df.loc[2, "Status"] = "Completed"

# unit_ops_df = reset_schedule(unit_ops_df, 1)

# unit_ops_df.loc[3, "Status"] = "Completed"

# unit_ops_df = reset_schedule(unit_ops_df, 1)

print(unit_ops_df)
# print(system_db["reactor"][0])
example.unit_ops_df = unit_ops_df

print("Wating for user input")
user_input = input("Enter your input: ")
print("Full steam ahead!!")


# launch_scheduled_ops(c9, t2, system_db, example)
# execute_scheduled_ops(c9, t2, system_db, example)
# t2.set_temp(0,0)

##################################
# full_unit_ops_df, overall_time = define_cp_job(unit_ops_df, 1)
# 
# print("Initial Schedule")
# print(full_unit_ops_df)
# full_unit_ops_df.loc[0, "Status"] = "Completed"
# 
# 
# 
# 
# 
# 
# unit_ops_df = full_unit_ops_df[full_unit_ops_df["Status"] == "To Do"]
# unit_ops_df = unit_ops_df.copy()
# unit_ops_df = unit_ops_df.reset_index(drop = True)
# print("After first task")
# print(unit_ops_df)
# 
# unit_ops_df, overall_time = define_cp_job(unit_ops_df, 1)
# print("Re-sheduled")
# print(unit_ops_df)
# 
# condition = full_unit_ops_df["Status"] == "To Do"
# sub_df = full_unit_ops_df.loc[condition, :]
# for row in sub_df.iterrows():
#     mask1 = unit_ops_df["Sample Name"] == row[1]["Sample Name"]
#     mask2 = unit_ops_df["UnitOP"] == row[1]["UnitOP"]
#     mask = mask1 & mask2
# 
#     full_unit_ops_df.loc[row[0],"Start Time (Ds)"] = unit_ops_df.loc[mask,"Start Time (Ds)"].values
#     full_unit_ops_df.loc[row[0],"End Time (Ds)"] = unit_ops_df.loc[mask,"End Time (Ds)"].values
# print(full_unit_ops_df)

#########################################

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

# execute_scheduled_ops(unit_ops_df, c9, t2, system_db, example)
# ops_launcher(job_list)
