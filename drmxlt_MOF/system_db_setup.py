from drmxlt_MOF.pipette_traking import *
from drmxlt_MOF.vial_tracking import *
from drmxlt_MOF.reactor_traking import *



system_db = {} # Container for information about the system

system_db['pipette_array'] = pipette_array #An array of pipette indexes in the shape of how they are layed out on the robot
system_db['pipette_order'] = pipette_order #A list of what order the pipettes should be used in
system_db['fresh_pipette'] = fresh_pipette #An array of which pipettes are still fresh and which are used - in the shape of pipette_array

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