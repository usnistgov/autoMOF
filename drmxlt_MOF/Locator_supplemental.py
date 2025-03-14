
from Locator import *
#TODO: Change add the heater block locations to Locator.py

heater_block_0 = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
heater_block_1 = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
heater_block_2 = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
heater_block_3 = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
heater_block_4 = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
heater_block_5 = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
heater_block_6 = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
heater_block_7 = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]


# Carousel Position for Syringe Pump Dispense to Clamp
# [Rotation, hieght]
pump_0 = [0, 0]
pump_1 = [0, 0]
pump_2 = [0, 0]
pump_3 = [135, 17]
pump_4 = [90, 17]
pump_5 = [45, 17]

#Offset the carusel to dispose into the waste bin
waste_disposal_offset = 90

#Pipetting hieghts
vial_rack_pipette_dispense_z = 150 #Height above vial for dispensing from pipette tip
vial_rack_pipette_draw_z = 130 #Height in vial for drawing into pipette tip
vial_rack_pipette_safe_z = 300 #Height above vial that's safely clear

vial_rack_pipette_zs = [vial_rack_pipette_dispense_z, vial_rack_pipette_draw_z, vial_rack_pipette_safe_z]

clamp_pipette_dispense_z = 200 #Height above vial for dispensing from pipette tip
clamp_pipette_draw_z = 180 #Height in vial for drawing into pipette tip
clamp_pipette_safe_z = 300 #Height above vial that's safely clear

clamp_pipette_zs = [clamp_pipette_dispense_z, clamp_pipette_draw_z, clamp_pipette_safe_z]

heater_block_pipette_dispense_z = 150 #Height above vial for dispensing from pipette tip
heater_block_pipette_draw_z = 130 #Height in vial for drawing into pipette tip
heater_block_pipette_safe_z = 300 #Height above vial that's safely clear

heater_block_pipette_zs = [heater_block_pipette_dispense_z, heater_block_pipette_draw_z, heater_block_pipette_safe_z]

################################################################################
'''
Zipcode system

0 => [Not on plaform, pre or post, 0]
1 => [Vial Rack, left or right, rack index 0-47]
2 => [gripper, 0, 0]
3 => [clamp, 0, 0]
4 => [heater, 0 to 7, heater index 0-3]
5 => [syringe pump, pump 1-3, splitter valve]  #note syringe pump 0 is in the arm

'''
################################################################################



def zip_to_pipette_z(zipcode):
  if zipcode[0] == 1: #vial rack
    zs = vial_rack_pipette_zs

  if zipcode[0] == 2: #gripper
    raise Exception("Gripper not valid location for pipetting")

  if zipcode[0] == 3: #clamp
    zs = clamp_pipette_zs

  if zipcode[0] == 4: #heater block
    zs = heater_block_pipette_zs

  if zipcode[0] == 5: #syringe pumps
    raise Exception("Syringe pumps not valid location for pipetting")

  return zs

def zip_to_locator(zipcode):
  "Look up the location from the zip code"

  if zipcode[0] == 1: #vial rack
    if zipcode[1] == 0: #left vial rack
      location = rack_left[zipcode[2]] #position in left vial rack

    elif zipcode[1] == 1: #right vial rack
      location = rack_right[zipcode[2]] #position in right vial rack
    else:
      raise Exception("Invalid rack location")

  if zipcode[0] == 2: #gripper
    raise Exception("Gripper not a fixed location")

  if zipcode[0] == 3: #clamp
    location = clamp

  if zipcode[0] == 4: #heater block
    if zipcode[1] == 0: #heater block 0
      location = heater_block_0[zipcode[2]] #position in heater block 0

    elif zipcode[1] == 1: #heater block 1
      location = heater_block_1[zipcode[2]] #position in heater block 1

    elif zipcode[1] == 2: #heater block 2
      location = heater_block_2[zipcode[2]] #position in heater block 2

    elif zipcode[1] == 3: #heater block 3
      location = heater_block_3[zipcode[2]] #position in heater block 3

    elif zipcode[1] == 4: #heater block 4
      location = heater_block_4[zipcode[2]] #position in heater block 4

    elif zipcode[1] == 5: #heater block 5
      location = heater_block_5[zipcode[2]] #position in heater block 5

    elif zipcode[1] == 6: #heater block 6
      location = heater_block_6[zipcode[2]] #position in heater block 6

    elif zipcode[1] == 7: #heater block 7
      location = heater_block_7[zipcode[2]] #position in heater block 7

    else:
      raise Exception("Invalid heater block location")

  if zipcode[0] == 5: #syringe pumps 
  ### NOTE: locations of syringe pumps are carousel positions rather than arm poses!!! #####
    if zipcode[1] == 0: #syringe pump 0
      location = pump_0

    elif zipcode[1] == 1: #syringe pump 1
      location = pump_1
    
    elif zipcode[1] == 2: #syringe pump 2
      location = pump_2

    elif zipcode[1] == 3: #syringe pump 3
      location = pump_3

    elif zipcode[1] == 4: #syringe pump 4
      location = pump_4

    elif zipcode[1] == 5: #syringe pump 5
      location = pump_5


  return location
