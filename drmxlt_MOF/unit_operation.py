import time
import numpy as np

from drmxlt_MOF.moving_vials import full_gripper_available_check, Violent_Action_Precheck, assign_sample_to_vial, Premove_Check_, Move_Sample, find_open_reactor_addresses, find_open_vial_rack_addresses
from drmxlt_MOF.fluid_dispensing import Fluid_dispense
from drmxlt_MOF.dummy_c9 import tare_balance
from drmxlt_MOF.im_proc import measure_color
from drmxlt_MOF.starting_reactors import hold_temp, temp_ramp_up_hold_down, Reactor_ready_check, read_temperature
from drmxlt_MOF.system_db_setup import machine_key_checkout, machine_key_release
from pyzbar.pyzbar import decode

# from drmxlt_MOF.Locator import camera_pos
from Locator import camera_pos, clamp, home, barcode_pos

import asyncio


def scan_barcode(Sample_ID, sample_db, c, cam, source=None, pickup= True, iteration = 0):

    if pickup == True:
        c.goto_safe(source)
        c.close_gripper()
    
    if iteration==0:
      c.goto_safe(barcode_pos)
    
    time.sleep(1)
    pic=cam.capture()
    time.sleep(1)
    pic.show()
    bcnum=decode(pic.img)
    if c.sim == True:
      bcnum = np.random.random()
      
    
    if iteration > 4:
        raise Exception("No Barcode detected")
    
    if not bcnum:
        print('no barcode detected')
        pos = c.get_axis_position(0)
        pos = c.counts_to_rad(0,pos)
        c.move_axis_rad(0, pos+2*np.pi/4, wait=True)
        scan_barcode(Sample_ID, sample_db, c, cam, source, pickup= False, iteration = iteration+1)
    else:
        c.reduce_axis_position(0)
        print(f"barcode = {bcnum}")
        vnum=int(bcnum[0].data)
        sample_db[Sample_ID]["Barcode"] = vnum

async def unit_op_sample_status(Sample_ID, experiment, unit_op_name, return_status = False):

  df = experiment.unit_ops_df

  status = df[(df["Sample Name"] == Sample_ID) &
              (df["UnitOP"] == unit_op_name)]["Status"].values[0]
  
  test = status == "Completed"

  if return_status == True:
    return status
  else:
    return test

async def update_unit_op_sample_status(Sample_ID, experiment, unit_op_name, new_status = "Completed"):
  df = experiment.unit_ops_df

  idx = df[(df["Sample Name"] == Sample_ID) &
           (df["UnitOP"] == unit_op_name)].index[0]
  
  df.loc[idx, "Status"] = new_status


async def unit_op_dependency(Sample_ID, experiment, unit_op_name, attempts_left = 5000):
  ready = unit_op_sample_status(Sample_ID, experiment, unit_op_name)

  if ready == True:
    return ready
  
  else:
    if attempts_left > 0:
      attempts_left -= 1

      await asyncio.sleep(0.2)
      return await unit_op_dependency(Sample_ID, experiment, unit_op_name, attempts_left)
    else:
      raise Exception(f"Dependency waiting on {unit_op_name} for sample {Sample_ID} timed out")


async def unit_op_preheat_status(reactor, target_temperature, experiment, return_status = False, tolerance = 5.0):
  
  df = experiment.unit_ops_df

  status = df[(df["UnitOP"] == "pre_heat_reactor") &
              (df["Reactor"] == reactor) &
              (df["Reactor Temperature (C)"] == target_temperature)]["Status"].values[0]
  
  test = status == "Completed"

  if type(status) != str:
    within_tol = np.abs(target_temperature - status) <= tolerance
    test = bool(test | within_tol)

  if return_status == True:
    return status
  else:
    return test




async def update_unit_op_preheat_status(reactor, target_temperature, experiment, t2, tolerance = 5.0):
  df = experiment.unit_ops_df

  idx = df[(df["UnitOP"] == "pre_heat_reactor") &
           (df["Reactor"] == reactor) &
           (df["Reactor Temperature (C)"] == target_temperature)].index[0]
  
  temperature = read_temperature(t2, reactor)

  within_tol = np.abs(target_temperature - temperature) <= tolerance

  if within_tol == True:
    df.loc[idx, "Status"] = "Completed"
  else:
    df.loc[idx, "Status"] = temperature


async def pre_heat_dependency_check(reactor, target_temperature, experiment):

  df = experiment.unit_ops_df

  #Find all the "react" unit ops that use the same reactor and have a lower temperature
  sub_df = df[(df["Reactor"] == reactor) &
              (df["UnitOP"] == "react") &
              (df["Reactor Temperature (C)"] < target_temperature)]
  
  #If there are any: 
  if len(sub_df) > 0:
    #Check the status of each of those
    status = sub_df["Status"].values
    #Have they all completed?
    test = all(status == "Completed")
  
  else:
    test = True
  
  return test

async def pre_heat_dependancy(reactor, target_temperature, experiment, attempts_left = 5000):

  ready = pre_heat_dependency_check(reactor, target_temperature, experiment)

  if ready == True:
    return ready
  
  else:
    if attempts_left > 0:
      attempts_left -= 0

      await asyncio.sleep(0.2)
      return await pre_heat_dependancy(reactor, target_temperature, experiment, attempts_left)
    else:
      raise Exception(f"Machine Reactor_{reactor} Not Available for PreHeat")


async def pre_heat_monitor(reactor, target_temperature, experiment, system_db, t, tolerance = 5.0, attempts_left = 5000):

  current_temp = read_temperature(t, reactor)

  update_unit_op_preheat_status(reactor, target_temperature, experiment, t, tolerance)

  #update system_db
  system_db['reactor'][reactor]["Temperature (C)"] = current_temp

  completed = unit_op_preheat_status(reactor, target_temperature, experiment, tolerance = tolerance)

  if completed == True:
    return completed
  else:
    if attempts_left > 0:
      attempts_left -= 1
      await asyncio.sleep(60)
      return await pre_heat_monitor(reactor, target_temperature, experiment, system_db, t, tolerance, attempts_left)
    else:
      raise Exception(f"Pre Heat Monitor for Reactor_{reactor} timed out")








async def Add_fluids(Sample_ID, c, cam, system_db, experiment, new_sample= True):
  #TODO: Add flag for sensitive dispensing (precursors, vs washing steps)
  print(f"Adding Fluids for {Sample_ID}")

  try:
    system_db = await machine_key_checkout(system_db, "Arm&Clamp")
    await update_unit_op_sample_status(Sample_ID, experiment, "add_fluids", "Running")

    #Read the sample id, determine precusor sources and volumes
    targetcomposition = experiment.find_compositions(Sample_ID)
    fluid_assignments = experiment.exp_fluid_resource_check(Sample_ID)

    #Check to make sure there are no violent actions on the system
    ## The shaking caused by the centrifuge or sonicator will add too much noise to the scale to weigh out precursors.
    violent_action = Violent_Action_Precheck(c)
    while violent_action == True:
      print("Waiting...")
      c.sonicator = False
      c.centrifuge = False
      time.sleep(5) # wait n seconds
      violent_action = Violent_Action_Precheck(c)

    #Assign the new sample to the vial
    if new_sample == True:
      assign_sample_to_vial(Sample_ID, experiment.sample_db, system_db)
      destination = np.array([2, 0, 0])
      Premove_Check_(Sample_ID, destination, experiment.sample_db, system_db, c)
      Move_Sample(Sample_ID, destination, experiment.sample_db, system_db, c)
      scan_barcode(Sample_ID, experiment.sample_db, c, cam, pickup=False)

    #Pre-move check
    destination = np.array([3, 0, 0]) #Want to move to the clamp
    Premove_Check_(Sample_ID, destination, experiment.sample_db, system_db, c)

    #Tare empty scale
    tare_balance(c)

    #Move vial to clamp
    Move_Sample(Sample_ID, destination, experiment.sample_db, system_db, c)

    #Un-cap
    c.close_clamp()
    system_db["clamp_status"] = "Closed"
    #TODO: push system db to Cordra
    c.close_gripper()
    c.uncap()
    c.move_z(300)
    c.open_clamp()
    system_db["clamp_status"] = "Open"
    #TODO: push system db to Cordra


    #Weigh empty vial
    if new_sample == True:
      empty_weight = c.read_steady_scale()
      experiment.sample_db[Sample_ID]["Empty Weight"] = empty_weight
      #TODO: push sample db to Cordra

    #Tare scale with empty vial
    tare_balance(c)

    #Dispense
    weighed_composition = {}
    for fluid in experiment.sample_db[Sample_ID]["Fluid Order"]:
      exp_vol = experiment.sample_db[Sample_ID]["Experiment Volumes (mL)"][fluid]
      Fluid_dispense(fluid, exp_vol, destination, c, experiment.fluid_db, system_db)
      weighed_composition[fluid] = c.read_steady_scale() 

    experiment.sample_db[Sample_ID]["Weighed Composition (g)"] = weighed_composition
    #TODO: push sample db to Cordra

    #Re-cap
    c.goto_xy_safe(clamp)
    c.close_clamp()
    system_db["clamp_status"] = "Closed"
    #TODO: push system db to Cordra
    c.move_z(186)
    c.cap(revs=2,torque_thresh=1650)
    c.open_clamp()
    system_db["clamp_status"] = "Open"
    #TODO: push system db to Cordra
      
    #Move to gripper
    destination = np.array([2, 0, 0]) #Want to move to the gripper
    Move_Sample(Sample_ID, destination, experiment.sample_db, system_db, c)

  finally: 
    system_db = await machine_key_release(system_db, "Arm&Clamp")
    await update_unit_op_sample_status(Sample_ID, experiment, "add_fluids", "Completed")

  return system_db

def Measure_color(Sample_ID, c, system_db, experiment):
  #Pre-move check
  destination = np.array([2, 0, 0]) #Want to move to the gripper
  Premove_Check_(Sample_ID, destination, experiment.sample_db, system_db, c)

  #Move vial to gripper
  Move_Sample(Sample_ID, destination, experiment.sample_db, system_db, c)

  #Move the arm to hold the sample infront of camera
  c.goto_safe(camera_pos)

  measure_color(Sample_ID, experiment.sample_db)

async def Preheat_reactor(reactor, target_temperature, c, t, system_db, experiment):
  print(f"Preheating Reactor {reactor}")
  if c.sim == True:
    return
  
  try: 
    #Is the reactor key available?
    system_db = await machine_key_checkout(system_db, f"Reactor_{reactor}")
    
    #Are there any reaction steps with this reactor, at a lower temperature, that haven't completed yet?
    ready = await pre_heat_dependancy(reactor, target_temperature, experiment)

    print(f"Preheat_reactor channel = {reactor}")
    hold_temp(t, reactor, target_temperature)

    #update the system db to capture the set temperature. 
    system_db["reactor"][reactor]["Set Temperature (C)"] = target_temperature
    #TODO: push system db to Cordra

    #pre_heat_monitor function will update the system_db and unit_ops_df until target temperature is reached.
    completed = await pre_heat_monitor(reactor, target_temperature, experiment, system_db, t)

  finally:
    system_db = await machine_key_release(system_db, f"Reactor_{reactor}")

  return system_db


async def Move_to_reactor(Sample_ID, c, system_db, experiment):
  print(f"Moving {Sample_ID} to reactor")
  try:
    sub_df = experiment.unit_ops_df[experiment.unit_ops_df["Sample Name"] == Sample_ID]
    sub_sub_df = sub_df[sub_df["UnitOP"] == "react"]
    reactor_ID = sub_sub_df["Reactor"].values[0]

    position = find_open_reactor_addresses(system_db, reactor_ID)

    destination = np.array([4, reactor_ID, position])

    #Check out the keys for the arm and for the reactor position:
    system_db = await machine_key_checkout(system_db, "Arm&Clamp")
    system_db = await machine_key_checkout(system_db, f"Reactor_{reactor_ID}", position)

    #Pre-move check
    Premove_Check_(Sample_ID, destination, experiment.sample_db, system_db, c)

    #Move vial to reactor
    Move_Sample(Sample_ID, destination, experiment.sample_db, system_db, c)

    c.goto_safe(home)

  finally:
    #Release the keys for the arm and for the reactor position:
    system_db = await machine_key_release(system_db, "Arm&Clamp")
    system_db = await machine_key_release(system_db, f"Reactor_{reactor_ID}", position)



async def Move_from_reactor(Sample_ID, c, system_db, experiment):
  print(f"Moving {Sample_ID} from reactor")
  try:
    sample_address = experiment.sample_db[Sample_ID]["Address"]
    reactor = sample_address[1]
    position = sample_address[2]

    #Check out the keys for the arm and for the reactor position:
    system_db = await machine_key_checkout(system_db, "Arm&Clamp")
    system_db = await machine_key_checkout(system_db, f"Reactor_{reactor}", position)

    destination = find_open_vial_rack_addresses(system_db)


    #Pre-move check
    Premove_Check_(Sample_ID, destination, experiment.sample_db, system_db, c)

    #Move vial to vial rack
    Move_Sample(Sample_ID, destination, experiment.sample_db, system_db, c)

  finally:
    #Release the keys for the arm and for the reactor position:
    system_db = await machine_key_release(system_db, "Arm&Clamp")
    system_db = await machine_key_release(system_db, f"Reactor_{reactor}", position)





# def Start_reaction(Sample_ID, destination, c, t, system_db, experiment, end_temp = 10):
async def Start_reaction(Sample_ID, c, t, system_db, experiment, end_temp = 10):
  print(f"Starting reaction for {Sample_ID}")
  if c.sim == True:
    return
  
  try:
    sample_address = experiment.sample_db[Sample_ID]["Address"]
    reactor = sample_address[1]
    reactor_pos = sample_address[2]

    system_db = await machine_key_checkout(system_db, f"Reactor_{reactor}", reactor_pos)

    sub_df = experiment.unit_ops_df[experiment.unit_ops_df["Sample Name"] == Sample_ID]
    sub_sub_df = sub_df[sub_df["UnitOP"] == "react"]
    reactor_id = sub_sub_df["Reactor"].values[0]
    target_temperature = experiment.sample_db[Sample_ID]["Temperature (C)"]
    reaction_time = experiment.sample_db[Sample_ID]["Reaction Time (min)"]

    #Reactor checks
    ready = True
    while ready == False:
      ready = Reactor_ready_check(t, reactor_id, target_temperature)
      time.sleep(20)

    #Record the reactor temperature
    # measured_temperature = t.get_temp(reactor_id)
    measured_temperature = read_temperature(t, reactor_id)
    system_db["reactor"][reactor_id]["Meas. Temperature (C)"] = measured_temperature
    #TODO: push system db to Cordra

    #Start reaction time
    print(f"Starting reaction.  Time: {reaction_time} s;  Temp: {target_temperature} degC;")
    # temp_ramp_up_hold_down(t, reactor_id, target_temperature, reaction_time, end_temp)
    hold_temp(t, reactor_id, target_temperature)
    print("Started reaction!")

    await asyncio.sleep(reaction_time * 60) #Wait for reaction_time (converted to seconds)

  finally:
    system_db = await machine_key_release(system_db, f"Reactor_{reactor}", reactor_pos)
    



async def React(Sample_ID, c, t, system_db, experiment):
  print(f"Starting react sequence for {Sample_ID}")

  #Wait for "add_fluids" for this sample to finish
  await unit_op_dependency(Sample_ID, experiment, "add_fluids")

  #Wait for the reactor pre_heat to finish
  sub_df = experiment.unit_ops_df[experiment.unit_ops_df["Sample Name"] == Sample_ID]
  sub_sub_df = sub_df[sub_df["UnitOP"] == "react"]
  reactor_id = sub_sub_df["Reactor"].values[0]
  target_temperature = sub_sub_df["Reactor Temperature (C)"].values[0]
  await pre_heat_dependancy(reactor_id, target_temperature, experiment)

  #Move sample to reactor
  await Move_to_reactor(Sample_ID, c, system_db, experiment)

  #Update the unit_ops_df
  await update_unit_op_sample_status(Sample_ID, experiment, "react", "Running")
  #Start the reaction
  await Start_reaction(Sample_ID, c, t, system_db, experiment)
  
  #Move sample from the reactor
  await Move_from_reactor(Sample_ID, c, system_db, experiment)
  
  #Update the unit_ops_df
  await update_unit_op_sample_status(Sample_ID, experiment, "react", "Completed")
  





def unwrap_unit_ops_df(unit_ops_df, c, t, cam, system_db, experiment ):
  unit_op_list = []

  for idx, row in unit_ops_df.iterrows():

      Sample_ID = row["Sample Name"]
      unit_op_type = row["UnitOP"]

      if unit_op_type == "pre_heat_reactor":
          reactor = row["Reactor"]
          target_temperature = row["Reactor Temperature (C)"]

          unit_op_task = [Preheat_reactor(reactor, target_temperature, c, t, system_db, experiment)]

      if unit_op_type == "add_fluids":
          unit_op_task = [Add_fluids(Sample_ID, c, cam, system_db, experiment)]

      if unit_op_type == "move_to_reactor":
          unit_op_task = [Move_to_reactor(Sample_ID, c, system_db, experiment)]

      if unit_op_type == "react":
          unit_op_task = [React(Sample_ID, c, t, system_db, experiment)]

      if unit_op_type == "move_from_reactor":
          unit_op_task = [Move_from_reactor(Sample_ID, c, system_db, experiment)]

      unit_op_list.append(unit_op_task[0])

  return unit_op_list


async def main(unit_ops_list):

  results = await asyncio.gather(*unit_ops_list, return_exceptions=True)

