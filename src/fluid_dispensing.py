
from .pipette_traking import get_next_pipette_tip, pip_rem
from .Locator_supplemental import zip_to_locator, zip_to_pipette_z, waste_disposal_offset
import north.n9_kinematics as n9
from Locator import home

from Locator import p_rack_right

def Pipette_Fluid(fluid, vol, source, destination, c, fluid_db, system_db, new_pipette_tip = True):
  #Genaric pipetting function to despense an arbitrary volume of fluid from 
  # arbitrary (and valid) source to an arbitrary (and valid) destination

  if all(source == destination):
    raise Exception("Source and destination are the same")

  # Can only pipette to and from the vial rack, the clamp, and the reactors
  #TODO put in a check for the reactor readyness
  in_vial_rack = source[0] == 1
  in_clamp = source[0] == 3
  in_reactor = source[0] == 4 

  test1 = in_vial_rack or in_clamp or in_reactor
  if test1 == False:
    raise Exception("Invalid source location for pipetting")

  dest_vial_rack = destination[0] == 1
  dest_clamp = destination[0] == 3
  dest_reactor = destination[0] == 4

  test2 = dest_vial_rack or dest_clamp or dest_reactor

  if test2 == False:
    raise Exception("Invalid destination location for pipetting")

  if new_pipette_tip == True:
    get_next_pipette_tip(system_db, c)
  # Pipete tip can only hold 1 ml at a time
  # So if the volume is more than 0.9 ml, dispense in 0.9 ml batches until it is less than that.

  if vol > 0.9:
    remaining_vol = vol - 0.9
    Pipette_Fluid(fluid, 0.9, source, destination, c, fluid_db, system_db, False)
    Pipette_Fluid(fluid, remaining_vol, source, destination, c, fluid_db, system_db, False)

  else:
    c.move_pump(0,0)
    
    source_location = zip_to_locator(source, tool="PipetteTip") #zip code to north location object
    source_zs = zip_to_pipette_z(source) #get the draw, dispense, and safe pipette arm z values for the source

    c.goto_xy_safe(source_location) #Move the arm above the source location
    c.move_z(source_zs[0]) #Move the pipette to draw hieght 

    c.set_pump_valve(0, c.PUMP_VALVE_RIGHT) # Set the pump valve draw fluid
    c.aspirate_ml(0, vol) #Draw fluid

    c.move_z(source_zs[2]) #Lift the pipette out of the vial
    c.set_pump_valve(0, c.PUMP_VALVE_RIGHT) # Set the pump valve draw fluid
    c.aspirate_ml(0, 0.1) #Draw 0.1 ml of air into pipette tip

    c.set_pump_valve(0, c.PUMP_VALVE_LEFT) # Set the pump valve to draw air from the lab side of syringe
    c.aspirate_ml(0, 0.9-vol) #Draw up to 0.9 ml of air

    destination_location = zip_to_locator(destination, tool="PipetteTip") # zip code to noth location object
    destination_zs = zip_to_pipette_z(destination) #get the draw, dispense, and safe pipette arm z values for the destination

    c.goto_safe(destination_location) #Move the arm above the destination location
    c.move_z(destination_zs[1]) #Move the pipette to dispense height

    c.set_pump_valve(0, c.PUMP_VALVE_RIGHT) # Set the pump valve dispense fluid
    c.dispense_ml(0, 0.999) #Dispense a full 1 ml (vol should be at most 0.9 ml)

    #update fluid_db
    fluid_db[fluid]['Volume (mL)'] = fluid_db[fluid]['Volume (mL)'] - vol
    #TODO: push fluid db to Cordra

    #move the arm out of the way
    c.goto_safe(home)


def current_pump_vol(c, pump_num):
    #Find the volume currently in the syringe pump
    
    vol = c.pumps[pump_num]['volume'] * c.pumps[pump_num]['pos'] / n9.PUMP_MAX_COUNTS
    
    return vol
    


def Syringe_Pump_Fluid(fluid, vol, source, c, fluid_db, waste = False):
  # Genaric function for dispensing fluid from the Syringe pumps
  # destination is assumed to be the clamp, unless despensing to waste for purging lines

  if source[0] != 5:
    raise Exception("Invalid source location for syringe pump")

  pump_num = source[1] # Get the pump number from the zip code
  syringe_vol = c.pumps[pump_num]['volume'] # Get the volume of that syringe pump
  

  carousel_pos = zip_to_locator(source)
  c.goto_safe(home)
  if vol > syringe_vol:
    Syringe_Pump_Fluid(fluid, syringe_vol, source, c, fluid_db, waste)
    Syringe_Pump_Fluid(fluid, vol-syringe_vol, source, c, fluid_db, waste)

  
  else:
    if waste == True:
      c.move_carousel(carousel_pos[0] + waste_disposal_offset, carousel_pos[1])

    else:
      c.move_carousel(carousel_pos[0], carousel_pos[1])
      
    current_vol = current_pump_vol(c, pump_num)

    c.set_pump_valve(pump_num, c.PUMP_VALVE_RIGHT) # Set the pump valve draw fluid
    c.aspirate_ml(pump_num, vol - current_vol) #Draw up fluid

    c.delay(0.2)

    c.set_pump_valve(pump_num, c.PUMP_VALVE_LEFT) # Set the pump valve dispense fluid
    c.dispense_ml(pump_num, vol) #Dispense 

    #update fluid_db
    fluid_db[fluid]['Volume (mL)'] = fluid_db[fluid]['Volume (mL)'] - vol
    #TODO: push fluid db to Cordra




def Fluid_dispense(fluid, exp_vol, destination, c, fluid_db, system_db):


  fluid_address = fluid_db[fluid]["Address"]

  if fluid_db[fluid]["Purged"] == False:
    Purge_fluid(fluid, c, fluid_db) 

  in_vial_rack = fluid_address[0] == 1
  in_clamp = fluid_address[0] == 3
  in_reactor = fluid_address[0] == 4
  test = in_vial_rack or in_clamp or in_reactor
  if test == True: #If the fluid is in the vial rack, clamp, or reactor
    Pipette_Fluid(fluid, exp_vol, fluid_address, destination, c, fluid_db, system_db)
    pip_rem(c) #Remove the pipette tip when done

  elif fluid_address[0] == 5: #If the fluid is in the syringe pump
    Syringe_Pump_Fluid(fluid, exp_vol, fluid_address, c, fluid_db)
    c.move_carousel(0,0) #move carousel home

def Purge_fluid(fluid, c, fluid_db):
  fluid_address = fluid_db[fluid]["Address"]

  purge_vol = fluid_db[fluid]["Purg Vol."]
  in_vial_rack = fluid_address[0] == 1
  in_clamp = fluid_address[0] == 3
  in_reactor = fluid_address[0] == 4
  test = in_vial_rack or in_clamp or in_reactor
  if test == True: #If the fluid is in the vial rack, clamp, or reactor
    # Pipette_Fluid(fluid, purge_vol, fluid_address, destination, c, fluid_db, system_db)
    #Pipette tips don't need to be purged
    pass

  elif fluid_address[0] == 5: #If the fluid is in the syringe pump
    #Purge lines by dispensing to waste
    Syringe_Pump_Fluid(fluid, purge_vol, fluid_address, c, fluid_db, waste=True)
    c.move_carousel(0,0) #move carousel home
    #Update fluid_db
    fluid_db[fluid]["Purged"] = True
    #TODO: push fluid db to Cordra
