
# from drmxlt_MOF.Locator import *
from Locator import *
#TODO: Change add the reactor locations to Locator.py

# reactor_0 = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
# reactor_1 = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
# reactor_2 = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
# reactor_3 = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
# reactor_4 = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
# reactor_5 = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
# reactor_6 = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
# reactor_7 = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]


# Carousel Position for Syringe Pump Dispense to Clamp
# [Rotation, hieght]
pump_0 = [0, 17] #Or make it error in trying to move the caroursel to pump 0
pump_1 = [225, 17]
pump_2 = [180, 17]
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

reactor_pipette_dispense_z = 150 #Height above vial for dispensing from pipette tip
reactor_pipette_draw_z = 130 #Height in vial for drawing into pipette tip
reactor_pipette_safe_z = 300 #Height above vial that's safely clear

reactor_pipette_zs = [reactor_pipette_dispense_z, reactor_pipette_draw_z, reactor_pipette_safe_z]

################################################################################
'''
Zipcode system

0 => [Not on plaform, pre or post, 0]
1 => [Vial Rack, left or right, rack index 0-47]
2 => [gripper, 0, 0]
3 => [clamp, 0, 0]
4 => [reactor, 0 to 7, reactor index 0-3]
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

  if zipcode[0] == 4: #reactor
    zs = reactor_pipette_zs

  if zipcode[0] == 5: #syringe pumps
    raise Exception("Syringe pumps not valid location for pipetting")

  return zs

def zip_to_locator(zipcode, tool = "Gripper"):
  #"Look up the location from the zip code"
  if tool == "Gripper":  
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
        location = vclamp

      if zipcode[0] == 4: #reactor
        if zipcode[1] == 0: #reactor 0
          location = reactor_0[zipcode[2]] #position in reactor 0
          # location = react0[zipcode[2]] #position in reactor 0

        elif zipcode[1] == 1: #reactor 1
          # location = reactor_1[zipcode[2]] #position in reactor 1
          location = react1[zipcode[2]] #position in reactor 1

        elif zipcode[1] == 2: #reactor 2
          location = reactor_2[zipcode[2]] #position in reactor 2
          # location = react2[zipcode[2]] #position in reactor 2

        elif zipcode[1] == 3: #reactor 3
          location = reactor_3[zipcode[2]] #position in reactor 3
          # location = react3[zipcode[2]] #position in reactor 3

        elif zipcode[1] == 4: #reactor 4
          location = reactor_4[zipcode[2]] #position in reactor 4
          # location = react4[zipcode[2]] #position in reactor 4

        elif zipcode[1] == 5: #reactor 5
          location = reactor_5[zipcode[2]] #position in reactor 5
          # location = react5[zipcode[2]] #position in reactor 5

        elif zipcode[1] == 6: #reactor 6
          location = reactor_6[zipcode[2]] #position in reactor 6
          # location = react6[zipcode[2]] #position in reactor 6

        elif zipcode[1] == 7: #reactor 7
          location = reactor_7[zipcode[2]] #position in reactor 7
          # location = react7[zipcode[2]] #position in reactor 7

        else:
          raise Exception("Invalid reactor location")

    
  #"Look up the location from the zip code"
  elif tool == "PipetteTip":  
      if zipcode[0] == 1: #vial rack
        if zipcode[1] == 0: #left vial rack
          location = p_rack_left[zipcode[2]] #position in left vial rack

        elif zipcode[1] == 1: #right vial rack
          location = p_rack_right[zipcode[2]] #position in right vial rack
        else:
          raise Exception("Invalid rack location")

      if zipcode[0] == 2: #gripper
        raise Exception("Gripper not a fixed location")

      if zipcode[0] == 3: #clamp
        location = s_clamp

      if zipcode[0] == 4: #reactor
        if zipcode[1] == 0: #reactor 0
          location = p_reactor_0[zipcode[2]] #position in reactor 0
          # location = p_react0[zipcode[2]] #position in reactor 0

        elif zipcode[1] == 1: #reactor 1
          location = p_reactor_1[zipcode[2]] #position in reactor 1
          # location = p_react1[zipcode[2]] #position in reactor 1

        elif zipcode[1] == 2: #reactor 2
          location = p_reactor_2[zipcode[2]] #position in reactor 2
          # location = p_react2[zipcode[2]] #position in reactor 2

        elif zipcode[1] == 3: #reactor 3
          location = reactor_3[zipcode[2]] #position in reactor 3
          # location = react3[zipcode[2]] #position in reactor 3

        elif zipcode[1] == 4: #reactor 4
          location = p_reactor_4[zipcode[2]] #position in reactor 4
          # location = p_react4[zipcode[2]] #position in reactor 4

        elif zipcode[1] == 5: #reactor 5
          location = p_reactor_5[zipcode[2]] #position in reactor 5
          # location = p_react5[zipcode[2]] #position in reactor 5

        elif zipcode[1] == 6: #reactor 6
          location = p_reactor_6[zipcode[2]] #position in reactor 6
          # location = p_react6[zipcode[2]] #position in reactor 6

        elif zipcode[1] == 7: #reactor 7
          location = p_reactor_7[zipcode[2]] #position in reactor 7
          # location = p_react7[zipcode[2]] #position in reactor 7

        else:
          raise Exception("Invalid reactor location")

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
