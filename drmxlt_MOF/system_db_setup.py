from drmxlt_MOF.pipette_traking import *
from drmxlt_MOF.vial_tracking import *
# from drmxlt_MOF.reactor_traking import *

from time import sleep
import asyncio

num_reactors = 8
positions_per_reactor = 4

positions_in_centrifuge = 6


system_db = {} # Container for information about the system

system_db['pipette_array'] = pipette_array #An array of pipette indexes in the shape of how they are layed out on the robot
system_db['pipette_order'] = pipette_order #A list of what order the pipettes should be used in
system_db['fresh_pipettes'] = fresh_pipettes #An array of which pipettes are still fresh and which are used - in the shape of pipette_array
system_db['needle_array'] = needle_array #An array of needle indexes in the shape of how they are layed out on the robot
system_db['needle_order'] = needle_order #A list of what order the pipettes should be used in
system_db['fresh_needles'] = fresh_needles #An array of which pipettes are still fresh and which are used - in the shape of pipette_array

system_db['vial_racks'] = ['rack_left', 'rack_right']
system_db['vial_rack_left_array'] = vial_rack_left_array
system_db['vial_rack_right_array'] = vial_rack_right_array
system_db['loaded_rack_left'], system_db['loaded_rack_right'] = loaded_vial_racks('left')
# system_db['loaded_rack_right'] = loaded_vial_racks('right')
system_db['left_rack_assignments'] = left_rack_assignments
system_db['right_rack_assignments'] = right_rack_assignments

system_db['gripper_occupied'] = False
system_db['clamp_status'] = "Closed"
system_db['clamp_assignment'] = "Empty"

system_db["arm_tool"] = "Empty"


#Setting up a dictionary to keep track of reactor status
reactor = {}

for i in range(num_reactors):
  reactor[i] = {"Block ID": i,
                     "Temperature (C)": None,
                     "Hat Status": "Off"}

  for j in range(positions_per_reactor):
    reactor[i][j] = {"Position": j,
                          "Assignment": "Empty"}
system_db["reactor"] = reactor

#Setting up a dictionary to keep track of centrifuge status
centrifuge = {}

for i in range(positions_in_centrifuge):
    centrifuge[i] = {"Position" : i,
                     "Assignment" : "Empty"}

half_turn = positions_in_centrifuge // 2

loading_order = []
for i in range(half_turn):
    loading_order.append(i)
    loading_order.append(i + half_turn)

centrifuge["Loading Order"] = loading_order

balast = {}
for i in range(3):
    balast[i] = {"Name" : f"Balast_{i}",
                 "Address" : np.array([1,1,i])}
    
    mask = system_db["vial_rack_right_array"] == i 
    system_db["loaded_rack_right"][mask] = 1
    system_db["right_rack_assignments"][mask] = f"Balast_{i}"

centrifuge["Balast"] = balast

system_db["centrifuge"] = centrifuge




system_db["KeyRing"] = {"Arm&Clamp": "Available"}

for reactor in range(num_reactors):
    new_reactor_key = f"Reactor_{reactor}"
    system_db["KeyRing"][new_reactor_key] = "Available"

    for position in range(positions_per_reactor):
        new_position_key = f"Reactor_{reactor}_{position}"
        system_db["KeyRing"][new_position_key] = "Available"

system_db["KeyRing"]["Centrifuge"] = "Available"
for position in range(positions_in_centrifuge):
    new_position_key = f"Centrifuge_{position}"
    system_db["KeyRing"][new_position_key] = "Available"

system_db["KeyRing"]["Sonicator"] = "Available"


async def machine_key_checkout(system_db, machine, component = None):
    """
    Asynchronous Function for waiting/depending checking out the key to a component of the system.
    
    Parameters
    ----------
    system_db : dict (-like)
        Database that tracks all the status of all components of the system
    machine : str
        Name of the machine in the KeyRing to checkout the keys for. 
    component : int
        Index specifying the sub-component of the machine

    Returns
    -------
    system_db : dict (-like)
        Updated Database that of all the statuses of all components of the system
    """

    available = False

    while available == False:
        await asyncio.sleep(0.2)
        available = machine_key_available(system_db, machine, component)

    if component == None:
            system_db["KeyRing"][machine] = "Occupied"
    else:
        component_key = machine + f"_{component}"
        system_db["KeyRing"][component_key] = "Occupied"
    return system_db
    

def machine_key_available(system_db, machine, component = None):
    """
    Function for checking availablity of the key to a component of the system.
    
    Parameters
    ----------
    system_db : dict (-like)
        Database that tracks all the status of all components of the system
    machine : str
        Name of the machine in the KeyRing to checkout the keys for. 
    component : int
        Index specifying the sub-component of the machine

    Returns
    -------
    available : bool
        Whether or not the key is available
    """
    if component == None:
        status = system_db["KeyRing"][machine]
    else:
        component_key = machine + f"_{component}"
        status = system_db["KeyRing"][component_key]

    available = status == "Available"

    return available


def machine_key_release(system_db, machine, component = None):
    """
    Function for releasing the key to a component of the system.
    
    Parameters
    ----------
    system_db : dict (-like)
        Database that tracks all the status of all components of the system
    machine : str
        Name of the machine in the KeyRing to checkout the keys for. 
    component : int
        Index specifying the sub-component of the machine

    Returns
    -------
    system_db : dict (-like)
        Updated Database that of all the statuses of all components of the system
    """

    if component == None:
        system_db["KeyRing"][machine] = "Available"
    else:
        component_key = machine + f"_{component}"
        system_db["KeyRing"][component_key] = "Available"


    return system_db

#TODO: push system db to Cordra? 
    #This is the function that initializes the system db
    #The main thread running the autonomous campaign simply imports this system_db object 

 