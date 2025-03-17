
from pipette_traking import get_next_pipette_tip
from Locator_supplemental import zip_to_locator, zip_to_pipette_z



def Pipette_Fluid(fluid, vol, source, destination, c, fluid_db):
  #Genaric pipetting function to despense an arbitrary volume of fluid from 
  # arbitrary (and valid) source to an arbitrary (and valid) destination

  if source == destination:
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


  # Pipete tip can only hold 1 ml at a time
  # So if the volume is more than 0.9 ml, dispense in 0.9 ml batches until it is less than that. 
  if vol > 0.9:
    remaining_vol = vol - 0.9
    Pipette_Fluid(0.9, source, destination)
    Pipette_Fluid(remaining_vol, source, destination)

  else:
    c.move_pump(0,0)
    get_next_pipette_tip()

    source_location = zip_to_locator(source) #zip code to north location object
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

    destination_location = zip_to_locator(destination) # zip code to noth location object
    destination_zs = zip_to_pipette_z(destination) #get the draw, dispense, and safe pipette arm z values for the destination

    c.goto_safe(destination) #Move the arm above the destination location
    c.move_z(destination_zs[1]) #Move the pipette to dispense height

    c.set_pump_valve(0, c.PUMP_VALVE_RIGHT) # Set the pump valve dispense fluid
    c.dispense_ml(0, 1) #Dispense a full 1 ml (vol should be at most 0.9 ml)

    #update fluid_db
    fluid_db[fluid]['Volume (mL)'] = fluid_db[fluid]['Volume (mL)'] - vol





def Syringe_Pump_Fluid(fluid, vol, source, c, fluid_db):
  # Genaric function for dispensing fluid from the Syringe pumps
  # destination is assumed to be the clamp

  if source[0] != 5:
    raise Exception("Invalid source location for syringe pump")

  pump_num = source[2] # Get the pump number from the zip code
  syringe_vol = c.pumps[pump_num]['volume'] # Get the volume of that syringe pump

  if vol > syringe_vol:
    Syringe_Pump_Fluid(syringe_vol, source)
    Syringe_Pump_Fluid(vol-syringe_vol, source)

  else:
    c.set_pump_valve(pump_num, c.PUMP_VALVE_RIGHT) # Set the pump valve draw fluid
    c.aspirate_ml(pump_num, vol) #Draw up fluid

    c.delay(0.2)

    c.set_pump_valve(pump_num, c.PUMP_VALVE_LEFT) # Set the pump valve dispense fluid
    c.aspirate_ml(pump_num, vol) #Draw up 0.1 ml of air

    #update fluid_db
    fluid_db[fluid]['Volume (mL)'] = fluid_db[fluid]['Volume (mL)'] - vol




def Fluid_dispense(fluid, exp_vol, fluid_db, destination):


  fluid_address = fluid_db[fluid]["Address"]

  in_vial_rack = fluid_address[0] == 1
  in_clamp = fluid_address[0] == 3
  in_reactor = fluid_address[0] == 4
  test = in_vial_rack or in_clamp or in_reactor
  if test == True: #If the fluid is in the vial rack, clamp, or reactor
    Pipette_Fluid(exp_vol, fluid_address, destination)

  elif fluid_address[0] == 5: #If the fluid is in the syringe pump
    Syringe_Pump_Fluid(exp_vol, fluid_address)

