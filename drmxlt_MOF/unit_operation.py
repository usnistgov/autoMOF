import time
import numpy as np

from drmxlt_MOF.moving_vials import full_gripper_available_check, Violent_Action_Precheck, assign_sample_to_vial, Premove_Check_, Move_Sample, find_open_reactor_addresses, find_open_vial_rack_addresses
from drmxlt_MOF.fluid_dispensing import Fluid_dispense
from drmxlt_MOF.dummy_c9 import tare_balance
from drmxlt_MOF.im_proc import measure_color
from drmxlt_MOF.starting_reactors import hold_temp, temp_ramp_up_hold_down, Reactor_ready_check, read_temperature
from drmxlt_MOF.system_db_setup import machine_key_checkout, machine_key_release
from drmxlt_MOF.op_launcher import write_db_files
from pyzbar.pyzbar import decode

# from drmxlt_MOF.Locator import camera_pos
from Locator import camera_pos, clamp, home, barcode_pos

import asyncio


def scan_barcode(Sample_ID, sample_db, c, cam, source=None, pickup= True, iteration = 0):
    """
    Function for scanning barcode of vial.
    Will try 4 iterations of rotating the vial to try to find the barcode.
    
    Parameters
    ----------
    Sample_ID : str
      Name of the sample
    sample_db : dict (-like)
      Database that tracks all the attributes of all the samples
    c : NorthC9
      NorthC9 object for instrument control
    cam : SimpleCamera
      north SimpleCamera object
    source : list
      list of 4 ints specifying robot arm pose
    pickup : bool
      flag for if the vial needs to be picked up
    iteration: int
      counter for how many attempts of scan_barcode() have ran


    Raises
    ------
    Exception
      If iterations excedes 4
    """

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


def unit_op_sample_status(Sample_ID, experiment, unit_op_name, return_status = False):
  """
  Function for querying the unit op database on the status of a task in the experiment.unit_ops_df object.
  
  Parameters
  ----------
  Sample_ID : str
    Name of the sample
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.
  unit_op_name : str
    The name of the unit op 
  return_status : bool
    Flag to return status or the result of test.

  Returns
  -------
  test : bool
    Whether or not the status is "Completed"
  status : str
    String discribing the status of the unit op
  """

  df = experiment.unit_ops_df

  status = df[(df["Sample Name"] == Sample_ID) &
              (df["UnitOP"] == unit_op_name)]["Status"].values[0]
  
  test = status == "Completed"

  if return_status == True:
    return status
  else:
    return test


def update_unit_op_sample_status(Sample_ID, experiment, unit_op_name, new_status = "Completed"):
  """
  Function for updating the unit op database on the status of a task in the experiment.unit_ops_df object.
  
  Parameters
  ----------
  Sample_ID : str
    Name of the sample
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.
  unit_op_name : str
    The name of the unit op 
  new_status : str
    String discribing the status of the unit op
  """

  df = experiment.unit_ops_df

  idx = df[(df["Sample Name"] == Sample_ID) &
           (df["UnitOP"] == unit_op_name)].index[0]
  
  df.loc[idx, "Status"] = new_status

  experiment.unit_ops_df = df
  return experiment


async def unit_op_dependency(Sample_ID, experiment, unit_op_name):
  """
  Asynchronous Function for waiting/depending for a task experiment.unit_ops_df object to be "Completed".
  
  Parameters
  ----------
  Sample_ID : str
    Name of the sample
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.
  unit_op_name : str
    The name of the unit op 

  Returns
  -------
  ready : bool
    Whether or not the status is "Completed"
  """
  
  ready = False

  while ready == False:
    await asyncio.sleep(0.2)
    ready = unit_op_sample_status(Sample_ID, experiment, unit_op_name)
  return ready



def unit_op_preheat_status(reactor, target_temperature, experiment, return_status = False, tolerance = 5.0):
  """
  Function for querying the unit op database on the status of a pre_heat task in the experiment.unit_ops_df object.
  Passes test if status is "Completed" or temperature is within tolerance. 
  
  Parameters
  ----------
  reactor : int
    Index of which reactor block to query 
  target_temperature : float
    Target temperature of this pre_heat task in degrees C
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.
  return_status : bool
    Flag to return status or the result of test.
  tolerance : float
    Tolerance on difference between measured temperature and target temperature to pass, in degreees C

  Returns
  -------
  test : bool
    Whether or not the status is "Completed"
  status : str
    String discribing the status of the unit op
  """
  
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


def update_unit_op_preheat_status(reactor, target_temperature, experiment, t2, tolerance = 5.0):
  """
  Function for updating the unit op database on the status of a pre_heat task in the experiment.unit_ops_df object.
  
  Parameters
  ----------
  reactor : int
    Index of which reactor block to query 
  target_temperature : float
    Target temperature of this pre_heat task in degrees C
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.
  t2 : NorthC9
    NorthC9 object for temperature control
  tolerance : float
    Tolerance on difference between measured temperature and target temperature to pass, in degreees C

  Returns
  -------
  experiment
    Updated Experiment object
  """
 
  df = experiment.unit_ops_df

  idx = df[(df["UnitOP"] == "pre_heat_reactor") &
           (df["Reactor"] == reactor) &
           (df["Reactor Temperature (C)"] == target_temperature)].index[0]
  
  temperature = read_temperature(t2, reactor)
  print(f"Pre_heat temperature {temperature}")

  within_tol = np.abs(target_temperature - temperature) <= tolerance

  if within_tol == True:
    df.loc[idx, "Status"] = "Completed"
  else:
    df.loc[idx, "Status"] = temperature

  experiment.unit_ops_df = df
  return experiment


def pre_heat_dependency_check(reactor, target_temperature, experiment):
  """
  Function for querying all the conditions for a pre_heat step.
  Any react steps with a lower temperature (that happen earlier) using the same reactor have to be "Completed"
  
  Parameters
  ----------
  reactor : int
    Index of which reactor block to query 
  target_temperature : float
    Target temperature of this pre_heat task in degrees C
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.

  Returns
  -------
  ready : bool
    Whether or not the status is "Completed"
  """
  df = experiment.unit_ops_df

  #Find all the "react" unit ops that use the same reactor and have a lower temperature
  sub_df = df[(df["Reactor"] == reactor) &
              (df["UnitOP"] == "react") &
              (df["Reactor Temperature (C)"] < target_temperature)]

  #If there are any: 
  if not sub_df.empty:
    #Check the status of each of those
    status = sub_df["Status"].values
    #Have they all completed?
    test = all(status == "Completed")
  
  else:
    test = True
  
  return test

async def pre_heat_dependancy(reactor, target_temperature, experiment):
  """
  Asynchronous Function for waiting/depending for all the conditions for a pre_heat step.
  
  Parameters
  ----------
  reactor : int
    Index of which reactor block to query 
  target_temperature : float
    Target temperature of this pre_heat task in degrees C
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.

  Returns
  -------
  ready : bool
    Whether or not the pre_heat step is ready to run
  """
  ready = False
  while ready == False:
    await asyncio.sleep(0.2)
    ready = pre_heat_dependency_check(reactor, target_temperature, experiment)
  return ready


async def pre_heat_monitor(reactor, target_temperature, experiment, system_db, t, tolerance = 5.0):
  """
  Asynchronous Function for monitoring the status of a pre_heat step.
  
  Parameters
  ----------
  reactor : int
    Index of which reactor block to query 
  target_temperature : float
    Target temperature of this pre_heat task in degrees C
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.
  t2 : NorthC9
    NorthC9 object for temperature control
  tolerance : float
    Tolerance on difference between measured temperature and target temperature to pass, in degreees C

  Returns
  -------
  experiment : Experiment
    A Experiment object with updated unit_ops_df status table.
  """

  completed = False
  while completed == False:
    
    await asyncio.sleep(1)

    current_temp = read_temperature(t, reactor)
    print(f"Pre_heat monitor current_temp {current_temp}")
    
    experiment = update_unit_op_preheat_status(reactor, target_temperature, experiment, t, tolerance)

    #update system_db
    system_db['reactor'][reactor]["Temperature (C)"] = current_temp

    completed = unit_op_preheat_status(reactor, target_temperature, experiment, tolerance = tolerance)

  return experiment



def add_fluids_dependancy_check(Sample_ID, experiment):
  """
  Function for querying all the conditions for a add_fluids step.
  Any pre_heat steps associated with this sample's react step, 
  must either be "Completed" or have a status that contains the Sample_ID
  
  Parameters
  ----------
  Sample_ID : str
    Name of the sample
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.

  Returns
  -------
  test : bool
    Whether or not the add_fluids step is ready to run
  """
  df = experiment.unit_ops_df

  #Find the index of the current op
  idx = df[(df["Sample Name"] == Sample_ID) &
          (df["UnitOP"] == "add_fluids")].index[0]
  
  #Find the op for this sample's reaction
  sub_df = df[(df["Sample Name"] == Sample_ID) &
              (df["UnitOP"] == "react")]
  reactor = sub_df["Reactor"].values[0]
  temperature = sub_df["Reactor Temperature (C)"].values[0]

  react_df = df[(df["UnitOP"] == "pre_heat_reactor") &
                (df["Reactor"] == reactor) &
                (df["Reactor Temperature (C)"] == temperature) &
                (df.index < idx)]
  if not react_df.empty:
    status = react_df["Status"].values[0]
    test1_1 = Sample_ID in status
    test1_2 = status == "Completed"
    test1 = test1_1 or test1_2
  else:
    test1 = True

  # Check the react ops that happen before this sample's reaction and wait for those to at least be "ending"
  #Find the index of pre-heat step for this samples reaction
  reactor_pre_heat_index = df[(df["UnitOP"] == "pre_heat_reactor") &
                              (df["Reactor"] == reactor) &
                              (df["Reactor Temperature (C)"] == temperature)].index[0]
  #Find all the statuses of the reactions at a different temperature that happen before this samples pre_heat step
  statuses = df[(df["UnitOP"] == "react") &
              (df["Reactor"] == reactor) &
              (df["Reactor Temperature (C)"] != temperature) &
              (df.index < reactor_pre_heat_index)]["Status"].values
  test2_1 = statuses == "Completed" 
  test2_2 = statuses == "Ending"
  test2 = all(test2_2 | test2_1) #all() returns True when both test1 and test2 are empty

  test = test1 and test2

  return test

async def add_fluids_dependency(Sample_ID, experiment):
    """
    Asynchronous Function for waiting/depending for all the conditions for a add_fluids step.
    
    Parameters
    ----------
    Sample_ID : str
        Name of the sample
    experiment : Experiment
        A Experiment object that contains all the information unique to this experiment.

    Returns
    -------
    test : bool
      Whether or not the add_fluids step is ready to run
    """
    ready = False

    while ready == False:
      await asyncio.sleep(1)
      ready = add_fluids_dependancy_check(Sample_ID, experiment)

    return ready


def react_dependency_check(Sample_ID, reactor, target_temperature, experiment, t2, tolerance = 5.0):
  """
  Function for querying the reactor block-based conditions for a react step.
  The temperature of the reactor block must be within tolerance.
  And the pre_heat step for this reactor and this temperature must either
  be "Completed" or have a status that contains the Sample_ID
  
  Parameters
  ----------
  Sample_ID : str
    Name of the sample
  reactor : int
    Index of which reactor block to query 
  target_temperature : float
    Target temperature of this pre_heat task in degrees C
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.
  t2 : NorthC9
    NorthC9 object for temperature control
  tolerance : float
    Tolerance on difference between measured temperature and target temperature to pass, in degreees C
  
  Returns
  -------
  test : bool
    Whether or not the react step is ready to run
  """
  if t2.sim == False:
    temperature = read_temperature(t2, reactor)

    within_tol = np.abs(target_temperature - temperature) <= tolerance
  else:
    within_tol = True
  

  pre_heat_status = unit_op_preheat_status(reactor, target_temperature, experiment, return_status = True, tolerance = tolerance)

  test2_1 = Sample_ID in pre_heat_status
  test2_2 = pre_heat_status == "Completed"
  test2 = test2_1 or test2_2

  test = within_tol and test2

  return test

async def react_dependancy(Sample_ID, reactor, target_temperature, experiment, t2, tolerance = 5.0):
  """
  Asynchronous Function for waiting/depending for all the conditions for a react step.
  
  Parameters
  ----------
  Sample_ID : str
    Name of the sample
  reactor : int
    Index of which reactor block to query 
  target_temperature : float
    Target temperature of this pre_heat task in degrees C
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.
  t2 : NorthC9
    NorthC9 object for temperature control
  tolerance : float
    Tolerance on difference between measured temperature and target temperature to pass, in degreees C
  
  Returns
  -------
  test : bool
    Whether or not the react step is ready to run
  """
  ready = False
  while ready == False:
    await asyncio.sleep(0.2)
    ready = react_dependency_check(Sample_ID, reactor, target_temperature, experiment, t2, tolerance)
  return ready





def initialize_sample(Sample_ID, c, cam, experiment, system_db, attempts_left = 96):
  """
  Function that tries to initialize a sample.
  1. assign a sample to next available vial
  2. move to the camera to scan the barcode
  3. If there is no barcode, set that vial back in the rack, mark that vial as "No Barcode", and try the next vial
  4. Keep trying until run out of available vials
  5. Update the experiment.sample_db to include the barcode
  
  Parameters
  ----------
  Sample_ID : str
    Name of the sample
  c : NorthC9
    NorthC9 object for instrument control
  cam : SimpleCamera
    north SimpleCamera object
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.
  system_db : dict (-like)
      Database that tracks all the status of all components of the system
  attempts_left: int
    counter for how many attempts of initialize_sample() can run


  Raises
  ------
  Exception
    If iterations excedes 4
  """
  try:
    assign_sample_to_vial(Sample_ID, experiment.sample_db, system_db)
    destination = np.array([2, 0, 0])
    Premove_Check_(Sample_ID, destination, experiment.sample_db, system_db, c)
    Move_Sample(Sample_ID, destination, experiment.sample_db, system_db, c)
    if c.sim == False:
      print("Scanning Barcode")
      scan_barcode(Sample_ID, experiment.sample_db, c, cam, pickup=False)
  except:
    #Move the sample back to the vial rack
    destination = find_open_vial_rack_addresses(system_db)
    Premove_Check_(Sample_ID, destination, experiment.sample_db, system_db, c)
    Move_Sample(Sample_ID, destination, experiment.sample_db, system_db, c)
    #Re assign that vial to "No Barcode"
    if destination[1] == 0:
      vial_array = system_db["vial_rack_left_array"]
      system_db["left_rack_assignments"][vial_array == destination[2]] = "No Barcode"
    elif destination[1] == 1:
        vial_array = system_db["vial_rack_right_array"]
        system_db["right_rack_assignments"][vial_array == destination[2]] = "No Barcode"
    #Reset that sample back to no assigned vial
    experiment.sample_db[Sample_ID]["Address"] = np.array([0, 0, 0])
    #And try again
    if attempts_left > 0:
      attempts_left -= 1
      initialize_sample(Sample_ID, c, cam, experiment, system_db, attempts_left)





async def Add_fluids(op_df_index, Sample_ID, c, cam, system_db, experiment, new_sample= True):
  """
  Asynchronous Function for adding fluids to vial
  1. await dependencies
  2. If this is a new sample, initialize it
  3. Move to the clamp
  4. Un-cap
  5. Dispense Fluids
  6. Re-cap
  7. Move to vial rack
  
  Parameters
  ----------
  op_df_index : int
    Index of this step in the unit_op_df
  Sample_ID : str
    Name of the sample
  c : NorthC9
    NorthC9 object for instrument control
  cam : SimpleCamera
    north SimpleCamera object
  system_db : dict (-like)
      Database that tracks all the status of all components of the system
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.
  new_sample: bool
    flag for whether or not the sample needs to be initiallized

  Awaits
  ------
  add_fluids_dependency(Sample_ID, experiment)
    awaits for the status of all the steps that this step depends on
  machine_key_checkout(system_db, "Arm&Clamp")
    awaits to check out the key for the Arm&Clamp

  Returns
  -------
  system_db : dict (-like)
      Updated database of all the statuses of all components of the system
  """
  #TODO: Add flag for sensitive dispensing (precursors, vs washing steps)
  

  ready = await add_fluids_dependency(Sample_ID, experiment)
  print(f"Op Index {op_df_index} system_db")
  print(system_db["KeyRing"])
  

  system_db = await machine_key_checkout(system_db, "Arm&Clamp")

  experiment = update_unit_op_sample_status(Sample_ID, experiment, "add_fluids", "Running")
  
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
    initialize_sample(Sample_ID, c, cam, experiment, system_db)



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
    
  #Move to vial rack
  destination = destination = find_open_vial_rack_addresses(system_db)
  Move_Sample(Sample_ID, destination, experiment.sample_db, system_db, c)

  system_db = machine_key_release(system_db, "Arm&Clamp")
  experiment = update_unit_op_sample_status(Sample_ID, experiment, "add_fluids", "Completed")

  print(f"Finished Op Index {op_df_index}")
  print(experiment.unit_ops_df)
  write_db_files(system_db, experiment)
  return system_db

def Measure_color(Sample_ID, c, system_db, experiment):
  #TODO Refactor as async function
  #Pre-move check
  destination = np.array([2, 0, 0]) #Want to move to the gripper
  Premove_Check_(Sample_ID, destination, experiment.sample_db, system_db, c)

  #Move vial to gripper
  Move_Sample(Sample_ID, destination, experiment.sample_db, system_db, c)

  #Move the arm to hold the sample infront of camera
  c.goto_safe(camera_pos)

  measure_color(Sample_ID, experiment.sample_db)

async def Preheat_reactor(op_df_index,reactor, target_temperature, c, t, system_db, experiment):
  """
  Asynchronous Function for pre heating the reactor block
  1. await dependencies
  2. sets reactor block to target temperature
  3. updates status to release samples after proper interval has elapsed  

  Parameters
  ----------
  op_df_index : int
    Index of this step in the unit_op_df
  reactor : int
    Index of which reactor block to address
  target_temperature : float
    Target temperature of this pre_heat task in degrees C
  c : NorthC9
    NorthC9 object for instrument control
  t : NorthC9
    NorthC9 object for temperature control
  system_db : dict (-like)
      Database that tracks all the status of all components of the system
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.

  Awaits
  ------
  pre_heat_dependancy(reactor, target_temperature, experiment)
    awaits for the status of all the steps that this step depends on
  machine_key_checkout(system_db, f"Reactor_{reactor}")
    awaits to check out the key for this reactor

  Returns
  -------
  system_db : dict (-like)
    Updated database of all the statuses of all components of the system
  experiment : Experiment 
    Updated Experiment object that contains all the information unique to this experiment.
  """
 
  #Are there any reaction steps with this reactor, at a lower temperature, that haven't completed yet?
  ready = await pre_heat_dependancy(reactor, target_temperature, experiment)
  
  print(f"Op Index {op_df_index} system_db")
  print(system_db["KeyRing"])

  #Is the reactor key available?
  system_db = await machine_key_checkout(system_db, f"Reactor_{reactor}")

  hold_temp(t, reactor, target_temperature)

  #update the system db to capture the set temperature. 
  system_db["reactor"][reactor]["Set Temperature (C)"] = target_temperature
  #TODO: push system db to Cordra

  #Update the pre-heat status to show what samples should start to add_fluids:
  df = experiment.unit_ops_df
  pre_heat_index = df[(df["Reactor"] == reactor) &
                      (df["UnitOP"] == "pre_heat_reactor") &
                      (df["Reactor Temperature (C)"] == target_temperature)].index[0]
  
  df.loc[pre_heat_index, "Status"] = "Running"

  #Find All the react unit ops at the same temperature with same reactor
  sub_df = df[(df["UnitOP"] == "react") &
            (df["Reactor Temperature (C)"] == target_temperature)]
  #Find the first start time of that reaction
  start_time = sub_df["Start Time (Ds)"].values[0]
  #Start a container of the released samples
  released_samples = []
  #Iterate through the react unit ops
  for idx, row in sub_df.iterrows():
      #Find the interval between the current start time and this row's start time
      interval = row["Start Time (Ds)"] - start_time
      
      await asyncio.sleep(interval * 10) #Sleep for that time (converted to seconds)
      # await asyncio.sleep(interval) # For quick simulations sleep for 1/10 time
      #Add that sample to the list of released samples
      released_samples.append(row["Sample Name"])
      print(f"Release Sample {released_samples}")
      #Update the status to release that sample
      df.loc[pre_heat_index, "Status"] = f"Release Sample {released_samples}"

      #Set the new start time to this row's start time
      start_time = row["Start Time (Ds)"] 

  df.loc[pre_heat_index, "Status"] = "Completed"

  system_db = machine_key_release(system_db, f"Reactor_{reactor}")

  print(f"Finished Op Index {op_df_index}")
  print(experiment.unit_ops_df)
  write_db_files(system_db, experiment)
  return system_db, experiment


async def Move_to_reactor(op_df_index, Sample_ID, c, system_db, experiment, destination):
  """
  Asynchronous Function for moving sample to reactor
  1. Move to the reactor destination
  
  Parameters
  ----------
  op_df_index : int
    Index of this step in the unit_op_df
  Sample_ID : str
    Name of the sample
  c : NorthC9
    NorthC9 object for instrument control
  system_db : dict (-like)
      Database that tracks all the status of all components of the system
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.
  destination: nd.array
    Address of the position on the reactor to move to

  Returns
  -------
  system_db : dict (-like)
      Updated database of all the statuses of all components of the system
  """
  print(f"Op Index {op_df_index}_sub 1 system_db")
  print(system_db["KeyRing"])
 

  #Pre-move check
  Premove_Check_(Sample_ID, destination, experiment.sample_db, system_db, c)

  #Move vial to reactor
  Move_Sample(Sample_ID, destination, experiment.sample_db, system_db, c)

  c.goto_safe(home)

  print(f"Finished Op Index {op_df_index} sub 1")
  print(experiment.unit_ops_df)
  return system_db



async def Move_from_reactor(op_df_index, Sample_ID, c, system_db, experiment):
  """
  Asynchronous Function for moving sample from reactor
  1. Move to the vial rack
  
  Parameters
  ----------
  op_df_index : int
    Index of this step in the unit_op_df
  Sample_ID : str
    Name of the sample
  c : NorthC9
    NorthC9 object for instrument control
  system_db : dict (-like)
      Database that tracks all the status of all components of the system
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.

  Returns
  -------
  system_db : dict (-like)
      Updated database of all the statuses of all components of the system
  """
  print(f"Op Index {op_df_index}_sub 3 system_db")
  print(system_db["KeyRing"])

  destination = find_open_vial_rack_addresses(system_db)


  #Pre-move check
  Premove_Check_(Sample_ID, destination, experiment.sample_db, system_db, c)

  #Move vial to vial rack
  Move_Sample(Sample_ID, destination, experiment.sample_db, system_db, c)

  c.goto_safe(home)

  print(f"Finished Op Index {op_df_index} sub 3")
  print(experiment.unit_ops_df)
  return system_db






async def Start_reaction(op_df_index, Sample_ID, c, t, system_db, experiment, end_temp = 10):
  """
  Asynchronous Function for starting reaction
  0. Pre_heat step already set the temperature indefinately, so no need to control the temperature
  1. Measure the temperature
  2. Sleep until nearing the end, and then update status to "Ending"
  3. Sleep for remaining time
  
  Parameters
  ----------
  op_df_index : int
    Index of this step in the unit_op_df
  Sample_ID : str
    Name of the sample
  c : NorthC9
    NorthC9 object for instrument control
  t : NorthC9
    NorthC9 object for temperature control
  system_db : dict (-like)
      Database that tracks all the status of all components of the system
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.
  end_temp : int|float
    Unused

  Awaits
  ------
  asyncio.sleep(reaction_time - time_nearing_end)
    Sleep until nearing the end: 4 mins or 10 % of reaction time, whatever's smaller
  asyncio.sleep(time_nearing_end)
    Sleep remaining time

  Returns
  -------
  system_db : dict (-like)
      Updated database of all the statuses of all components of the system
  """
  
  print(f"Op Index {op_df_index}_sub 2 system_db")
  print(system_db["KeyRing"])
 
  print(f"Starting reaction for {Sample_ID}")

  sub_df = experiment.unit_ops_df[experiment.unit_ops_df["Sample Name"] == Sample_ID]
  sub_sub_df = sub_df[sub_df["UnitOP"] == "react"]
  reactor_id = sub_sub_df["Reactor"].values[0]
  target_temperature = experiment.sample_db[Sample_ID]["Temperature (C)"]
  reaction_time = experiment.sample_db[Sample_ID]["Reaction Time (min)"]



  #Start reaction time
  if c.sim == False:
    print("Started reaction!")
    #Record the reactor temperature
    measured_temperature = read_temperature(t, reactor_id)
    system_db["reactor"][reactor_id]["Meas. Temperature (C)"] = measured_temperature
    #TODO: push system db to Cordra

  #Seconds before the ending to consider nearing the end
  time_nearing_end = np.min([4 * 60, 0.1 * reaction_time]) # 4 min or 10% of reaction time, whatever's smaller
  await asyncio.sleep(reaction_time * 60 - time_nearing_end) #Wait for reaction_time (converted to seconds)
  
  #Update the unit_ops_df
  experiment = update_unit_op_sample_status(Sample_ID, experiment, "react", "Ending")
  print(f"Nearing End of react {Sample_ID}")
  print(experiment.unit_ops_df)
  await asyncio.sleep(time_nearing_end) #Wait rest of the time

  print(f"Finished Op Index {op_df_index} sub 2")
  print(experiment.unit_ops_df)
  return system_db
    



async def React(op_df_index,Sample_ID, c, t, system_db, experiment):
  """
  Asynchronous Function for react macro
  0. Pre_heat step already set the temperature indefinately, so no need to control the temperature
  1. await dependencies
  2. Move to reactor
  3. Start reaction
  4. Move from reactor
  
  Parameters
  ----------
  op_df_index : int
    Index of this step in the unit_op_df
  Sample_ID : str
    Name of the sample
  c : NorthC9
    NorthC9 object for instrument control
  t : NorthC9
    NorthC9 object for temperature control
  system_db : dict (-like)
      Database that tracks all the status of all components of the system
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.

  Awaits
  ------
  unit_op_dependency(Sample_ID, experiment, "add_fluids")
    Awaits the add_fluids step for this sample to be "Completed"
  react_dependancy(reactor, target_temperature, experiment)
    awaits for the status of all the reactor block-based steps that this step depends on
  machine_key_checkout(system_db, "Arm&Clamp")
    awaits to check out the key for this reactor
  machine_key_checkout(system_db, f"Reactor_{reactor_id}", position)
    awaits to check out the key for available position of this reactor
  Move_to_reactor(op_df_index,Sample_ID, c, system_db, experiment, destination)
    awaits the sample moving to the reactor
  Start_reaction(op_df_index,Sample_ID, c, t, system_db, experiment)
    awaits the reaction of the sample 
  machine_key_checkout(system_db, "Arm&Clamp")
    awaits to check out the key for this reactor
  Move_from_reactor(op_df_index, Sample_ID, c, system_db, experiment)
    awaits the sample moving to the reactor

  Returns
  -------
  system_db : dict (-like)
    Updated database of all the statuses of all components of the system
  experiment : Experiment 
    Updated Experiment object that contains all the information unique to this experiment.
  sample_ready : bool
    Flag for passing the dependency on the add_fluids 
  reactor_preheated : bool
    Flag for passing the dependency on the pre_heating step 
  """

  print(f"Testing {Sample_ID} react dependencies")
  #Wait for "add_fluids" for this sample to finish
  sample_ready = await unit_op_dependency(Sample_ID, experiment, "add_fluids")
  print(f"Passed {Sample_ID} dependencies on add fluids")

  #Wait for the reactor pre_heat to finish
  sub_df = experiment.unit_ops_df[experiment.unit_ops_df["Sample Name"] == Sample_ID]
  sub_sub_df = sub_df[sub_df["UnitOP"] == "react"]
  reactor_id = sub_sub_df["Reactor"].values[0]
  target_temperature = sub_sub_df["Reactor Temperature (C)"].values[0]
  reactor_preheated = await react_dependancy(Sample_ID, reactor_id, target_temperature, experiment, t)
  print(f"Passed {Sample_ID} dependencies on pre_heat")

  #Check out the keys for the arm and for the reactor position:
  system_db = await machine_key_checkout(system_db, "Arm&Clamp")
  position = find_open_reactor_addresses(system_db, reactor_id)
  destination = np.array([4, reactor_id, position])  
  system_db = await machine_key_checkout(system_db, f"Reactor_{reactor_id}", position)

  print(f"Op Index {op_df_index} system_db")
  print(system_db["KeyRing"])
  
  #Update the unit_ops_df
  experiment = update_unit_op_sample_status(Sample_ID, experiment, "react", "Running")

  #Move sample to reactor
  system_db = await Move_to_reactor(op_df_index,Sample_ID, c, system_db, experiment, destination)
  # Release Key for Arm&Clamp
  system_db = machine_key_release(system_db, "Arm&Clamp")
  write_db_files(system_db, experiment)

  #Start the reaction
  system_db = await Start_reaction(op_df_index,Sample_ID, c, t, system_db, experiment)
  write_db_files(system_db, experiment)
  
  #Move sample from the reactor
  system_db = await machine_key_checkout(system_db, "Arm&Clamp")
  system_db = await Move_from_reactor(op_df_index, Sample_ID, c, system_db, experiment)

  #Release the Keys for Arm&Clamp and Reactor Postion
  system_db = machine_key_release(system_db, "Arm&Clamp")
  system_db = machine_key_release(system_db, f"Reactor_{reactor_id}", position)

  #Update the unit_ops_df
  experiment = update_unit_op_sample_status(Sample_ID, experiment, "react", "Completed")
  print(f"Finished Op Index {op_df_index}")
  print(experiment.unit_ops_df)
  write_db_files(system_db, experiment)
  return system_db, experiment, sample_ready, reactor_preheated 





def unwrap_unit_ops_df(unit_ops_df, c, t, cam, system_db, experiment ):
  """
  Function for reading the unit_ops_df and converting to list of tasks
  
  Parameters
  ----------
  Sample_ID : str
    Name of the sample
  c : NorthC9
    NorthC9 object for instrument control
  t : NorthC9
    NorthC9 object for temperature control
  cam : SimpleCamera
    north SimpleCamera object
  system_db : dict (-like)
      Database that tracks all the status of all components of the system
  experiment : Experiment
    A Experiment object that contains all the information unique to this experiment.

  Returns
  -------
  unit_op_list : list
    List of all the tasks in the unit_ops_df
  """
  
  unit_op_list = []
  
  for idx, row in unit_ops_df.iterrows():

      Sample_ID = row["Sample Name"]
      unit_op_type = row["UnitOP"]

      if unit_op_type == "pre_heat_reactor":
          reactor = row["Reactor"]
          target_temperature = row["Reactor Temperature (C)"]

          unit_op_task = [Preheat_reactor(idx, reactor, target_temperature, c, t, system_db, experiment)]

      if unit_op_type == "add_fluids":
          unit_op_task = [Add_fluids(idx, Sample_ID, c, cam, system_db, experiment)]

      if unit_op_type == "react":
          unit_op_task = [React(idx, Sample_ID, c, t, system_db, experiment)]


      unit_op_list.append(unit_op_task[0])
  print("UnitOPs =", len(unit_op_list))
  return unit_op_list


async def main(unit_ops_list):
  """
  Asynchronous Function for running all the tasks in the unit_ops_list
  
  Parameters
  ----------
  unit_op_list : list
    List of all the tasks in the unit_ops_df

  Returns
  -------
  results
    List of all the results from all the tasks
  """

  results = await asyncio.gather(*unit_ops_list, return_exceptions=True)
  return results

