import sys
sys.path.append("C://Users//asm6//drmxlt//drmxlt//")

from drmxlt_MOF.experiments import Ternary_colordemo, Cu_BTC
from drmxlt_MOF.moving_vials import Move_Sample, find_open_vial_rack_addresses, Premove_Check_, find_open_reactor_addresses
from drmxlt_MOF.moving_vials import force_Move_Vial
from drmxlt_MOF.unit_operation import Add_fluids
from drmxlt_MOF.system_db_setup import system_db, machine_key_checkout, machine_key_release, machine_key_available
from drmxlt_MOF.op_scheduler import create_unit_ops_df, assign_reactors, define_cp_job, reset_schedule
from drmxlt_MOF.op_launcher import launch_scheduled_ops, execute_scheduled_ops
from north import NorthC9
import json
from drmxlt_MOF.dummy_c9 import dummy_c9


from north_simple_camera import SimpleCamera, SimplePhoto
import time
from time import sleep

import asyncio


async def use_arm_clamp(system_db, task_id):
    """Task that uses 'Arm&Clamp'."""
    try:
        system_db = await machine_key_checkout(system_db, "Arm&Clamp")
        print(f"Task {task_id} using Arm&Clamp")
        await asyncio.sleep(30)  # Simulate work
    finally:
        system_db = await machine_key_release(system_db, "Arm&Clamp")
        print(f"Task {task_id} released Arm&Clamp")
    return system_db

async def use_reactor_0_0(system_db, task_id):
    """Task that uses 'Reactor_0' component 0."""
    try:
        system_db = await machine_key_checkout(system_db, "Reactor_0", 0)
        print(f"Task {task_id} using Reactor_0_0")
        await asyncio.sleep(30)  # Simulate work
    finally:
        system_db = await machine_key_release(system_db, "Reactor_0", 0)
        print(f"Task {task_id} released Reactor_0_0")
    return system_db


async def main():

    tasks = [
        use_arm_clamp(system_db, 1),
        use_arm_clamp(system_db, 2),
        use_reactor_0_0(system_db, 3)
    ]


    # Run tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Check for exceptions
    for result in results:
        if isinstance(result, Exception):
            print(f"Task raised an exception: {result}")

start_time = time.perf_counter()
print(system_db["KeyRing"])

asyncio.run(main())

end_time = time.perf_counter()
elapsed_time = end_time - start_time
print(f"Operations completed in {elapsed_time:.4f} seconds (wall-clock time).")

print("DONE")
print(system_db["KeyRing"])