from drmxlt_MOF.pipette_traking import *
from drmxlt_MOF.vial_tracking import *
from drmxlt_MOF.reactor_traking import *

from time import sleep
import asyncio

system_db = {} # Container for information about the system

system_db['pipette_array'] = pipette_array #An array of pipette indexes in the shape of how they are layed out on the robot
system_db['pipette_order'] = pipette_order #A list of what order the pipettes should be used in
system_db['fresh_pipettes'] = fresh_pipettes #An array of which pipettes are still fresh and which are used - in the shape of pipette_array

system_db['vial_racks'] = ['rack_left', 'rack_right']
system_db['vial_rack_left_array'] = vial_rack_left_array
system_db['vial_rack_right_array'] = vial_rack_right_array
system_db['loaded_rack_left'] = loaded_vial_racks('left')
system_db['loaded_rack_right'] = loaded_vial_racks('right')
system_db['left_rack_assignments'] = left_rack_assignments
system_db['right_rack_assignments'] = right_rack_assignments

system_db['gripper_occupied'] = False
system_db['clamp_status'] = "Closed"
system_db['clamp_assignment'] = "Empty"

system_db["reactor"] = reactor


system_db["KeyRing"] = {"Arm&Clamp": "Available",
                        "Reactor_0": "Available",
                        "Reactor_0_0": "Available",
                        "Reactor_0_1": "Available",
                        "Reactor_0_2": "Available",
                        "Reactor_0_3": "Available",
                        "Reactor_1": "Available",
                        "Reactor_1_0": "Available",
                        "Reactor_1_1": "Available",
                        "Reactor_1_2": "Available",
                        "Reactor_1_3": "Available",
                        "Centrifuge": "Available",
                        "Centrifuge_0": "Available",
                        "Centrifuge_1": "Available",
                        "Sonicator": "Available"}


async def machine_key_checkout(system_db, machine, component = None, attempts_left = 5000):
    
    available = machine_key_available(system_db, machine, component)

    if available == True:

        if component == None:
            system_db["KeyRing"][machine] = "Occupied"
        else:
            component_key = machine + f"_{component}"
            system_db["KeyRing"][component_key] = "Occupied"
        return system_db
    
    if available == False:
        if attempts_left > 0:
            attempts_left -= 1
            # await asyncio.sleep(20)
            await asyncio.sleep(0.2)
            # print("sleeping")
            return await machine_key_checkout(system_db, machine, component, attempts_left)
        else:
            raise Exception(f"Machine {machine}_{component} Not Available")

def machine_key_available(system_db, machine, component = None):
    if component == None:
        status = system_db["KeyRing"][machine]
    else:
        component_key = machine + f"_{component}"
        status = system_db["KeyRing"][component_key]

    available = status == "Available"

    return available


async def machine_key_release(system_db, machine, component = None):

    if component == None:
        system_db["KeyRing"][machine] = "Available"
    else:
        component_key = machine + f"_{component}"
        system_db["KeyRing"][component_key] = "Available"


    return system_db

#TODO: push system db to Cordra? 
    #This is the function that initializes the system db
    #The main thread running the autonomous campaign simply imports this system_db object 

# def update_system_db(system_db, alt_db):
#   #Read the alt_db for addresses and use that to update system_db

#   for key in alt_db.keys():
#     address = alt_db[key]["Address"]

#     if address[0] == 1: #if the fluid is in the vial rack
#       if address[1] == 0: #if the fluid is in the left vial rack
#         mask = system_db["vial_rack_left_array"] == address[2]
#         system_db["left_rack_assignments"][mask] = key

#       if address[1] == 1: #if the fluid is in the right vial rack
#         mask = system_db["vial_rack_right_array"] == address[2]
#         system_db["right_rack_assignments"][mask] = key

#   return system_db