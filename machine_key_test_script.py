import sys
# sys.path.append("C://Users//asm6//drmxlt//drmxlt//")
sys.path.append("C://Users//drmxlt//Documents//Cu_BTC_synth_control_test//")

import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

from drmxlt_MOF.experiments import Ternary_colordemo, Cu_BTC
from drmxlt_MOF.moving_vials import Move_Sample, find_open_vial_rack_addresses, Premove_Check_, find_open_reactor_addresses
from drmxlt_MOF.moving_vials import force_Move_Vial
from drmxlt_MOF.unit_operation import Add_fluids, unwrap_unit_ops_df, main
from drmxlt_MOF.system_db_setup import system_db, machine_key_checkout, machine_key_release, machine_key_available
from drmxlt_MOF.op_scheduler import create_unit_ops_df, assign_reactors, define_cp_job, reset_schedule, interleave_reactor_preheating
from drmxlt_MOF.op_launcher import launch_scheduled_ops, execute_scheduled_ops
from north import NorthC9
import json
from drmxlt_MOF.dummy_c9 import dummy_c9


from north_simple_camera import SimpleCamera, SimplePhoto
import time
from time import sleep

import asyncio

# c9 = NorthC9(addr="sim")
c9 = NorthC9('A',network_serial="AU06D2C0")  # instantiate a C9 controller object with C9 network address A-

# c9.default_vel=15
c9.default_vel=7

t2=NorthC9('B',network=c9.network)

sleep(0.2)
cam = SimpleCamera(0)
sleep(0.2)

example = Cu_BTC()
# c9 = dummy_c9()
# t2 = c9
# cam = c9
num_reactors = 1

unit_ops_df = create_unit_ops_df(example.sample_db, True, True, False, False, False)
print("Created Unit Ops DF")

unit_ops_df, reactor_df = assign_reactors(unit_ops_df, num_reactors, 4)
print("Assigned Reactors")

unit_ops_df, overall_time = define_cp_job(unit_ops_df, num_reactors)
print("Solved Constraint Satisfaction Problem")

unit_ops_df = interleave_reactor_preheating(unit_ops_df, 10)
print("Interleaved preheating")

print(unit_ops_df)

example.unit_ops_df = unit_ops_df
example.reactor_df = reactor_df



print("Starting main")
asyncio.run(main(unwrap_unit_ops_df(unit_ops_df, c9, t2, cam, system_db, example)))

print(system_db["KeyRing"])


###############################################################################
###############################################################################

# async def use_arm_clamp(system_db, task_id):
#     """Task that uses 'Arm&Clamp'."""
#     try:
#         system_db = await machine_key_checkout(system_db, "Arm&Clamp")
#         print(f"Task {task_id} using Arm&Clamp")
#         await asyncio.sleep(30)  # Simulate work
#     finally:
#         system_db = await machine_key_release(system_db, "Arm&Clamp")
#         print(f"Task {task_id} released Arm&Clamp")
#     return system_db

# async def use_reactor_0_0(system_db, task_id):
#     """Task that uses 'Reactor_0' component 0."""
#     try:
#         system_db = await machine_key_checkout(system_db, "Reactor_0", 0)
#         print(f"Task {task_id} using Reactor_0_0")
#         await asyncio.sleep(30)  # Simulate work
#     finally:
#         system_db = await machine_key_release(system_db, "Reactor_0", 0)
#         print(f"Task {task_id} released Reactor_0_0")
#     return system_db


# async def main():

#     tasks = [
#         use_arm_clamp(system_db, 1),
#         use_arm_clamp(system_db, 2),
#         use_reactor_0_0(system_db, 3)
#     ]


#     # Run tasks concurrently
#     results = await asyncio.gather(*tasks, return_exceptions=True)

#     # Check for exceptions
#     for result in results:
#         if isinstance(result, Exception):
#             print(f"Task raised an exception: {result}")

# start_time = time.perf_counter()
# print(system_db["KeyRing"])

# asyncio.run(main())

# end_time = time.perf_counter()
# elapsed_time = end_time - start_time
# print(f"Operations completed in {elapsed_time:.4f} seconds (wall-clock time).")

# print("DONE")
# print(system_db["KeyRing"])