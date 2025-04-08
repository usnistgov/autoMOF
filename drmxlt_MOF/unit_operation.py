import time
import numpy as np

from drmxlt_MOF.moving_vials import full_gripper_available_check, Violent_Action_Precheck, assign_sample_to_vial, Premove_Check_, Move_Sample
from drmxlt_MOF.fluid_dispensing import Fluid_dispense
from drmxlt_MOF.dummy_c9 import tare_balance
from drmxlt_MOF.im_proc import measure_color
from starting_reactors import hold_temp, temp_ramp_up_hold_down, Reactor_ready_check

from drmxlt_MOF.Locator import camera_pos


def Add_fluids(Sample_ID, c, system_db, experiment, new_sample= True):
  #TODO: Add flag for sensitive dispensing (precursors, vs washing steps)


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
  c.uncap()
  c.move_z(300)
  c.open_clamp()
  system_db["clamp_status"] = "Open"


  #Weigh empty vial
  if new_sample == True:
    empty_weight = c.read_steady_scale()
    experiment.sample_db[Sample_ID]["Empty Weight"] = empty_weight

  #Tare scale with empty vial
  tare_balance(c)

  #Dispense
  weighed_composition = {}
  for fluid in experiment.sample_db[Sample_ID]["Fluid Order"]:

    exp_vol = experiment.sample_db[Sample_ID]["Experiment Volumes (mL)"][fluid]
    Fluid_dispense(fluid, exp_vol, destination, c, experiment.fluid_db, system_db)
    weighed_composition[fluid] = c.read_steady_scale() 

  experiment.sample_db[Sample_ID]["Weighed Composition (g)"] = weighed_composition
  #TODO: push sample and fluid dbs to Cordra

  #Re-cap
  c.close_clamp()
  system_db["clamp_status"] = "Closed"
  c.uncap()
  c.move_z(300)
  c.open_clamp()
  system_db["clamp_status"] = "Open"
    

  #Move to gripper
  destination = np.array([2, 0, 0]) #Want to move to the gripper
  Move_Sample(Sample_ID, destination, experiment.sample_db, system_db, c)

def Measure_color(Sample_ID, c, system_db, experiment):
  #Pre-move check
  destination = np.array([2, 0, 0]) #Want to move to the gripper
  Premove_Check_(Sample_ID, destination, experiment.sample_db, system_db, c)

  #Move vial to gripper
  Move_Sample(Sample_ID, destination, experiment.sample_db, system_db, c)

  #Move the arm to hold the sample infront of camera
  c.goto_safe(camera_pos)

  measure_color(Sample_ID, experiment.sample_db)


def Preheat_reactor(Sample_ID, address, c, t, system_db, experiment):
  target_temperature = experiment.sample_db[Sample_ID]["Temperature (C)"]

  reactor_id = address[1] #Find the reactor ID from the zip code

  hold_temp(t, reactor_id, target_temperature)

  #update the system db to capture the set temperature. 
  system_db["reactor"][reactor_id]["Set Temperature (C)"] = target_temperature


def Start_reaction(Sample_ID, destination, c, t, system_db, experiment, end_temp = 20):
  reactor_id = destination[1]
  target_temperature = experiment.sample_db[Sample_ID]["Temperature (C)"]
  reaction_time = experiment.sample_db[Sample_ID]["Reaction Time (min)"]

  #Reactor checks
  ready = False
  while ready == False:
    ready = Reactor_ready_check(t, reactor_id, target_temperature)
    time.sleep(20)

  #Record the reactor temperature
  measured_tempeature = t.get_temp(reactor_id)
  system_db["reactor"][reactor_id]["Meas. Temperature (C)"] = measured_tempeature

  #Pre-move check
  Premove_Check_(Sample_ID, destination, experiment.sample_db, system_db, c)

  #Move vial to reactor
  Move_Sample(Sample_ID, destination, experiment.sample_db, system_db, c)

  #Start reaction time
  temp_ramp_up_hold_down(t, reactor_id, target_temperature, reaction_time, end_temp)
  

class UnitOP_table():
  """Each sample will have a fixed set of unit ops in a particular order
  Each operation will occupy the Arm&Clamp for some amount of time.
    Arm&Clamp is considered one unit (to put the sample in the reactor we need the arm, but we also need the clamp so we can loosen the cap of the vial)
  Each operation could also occupy a reactor, the centrifuge, and or the sonicator for some amount of time."""
  
  Sample_IDs = []
  UnitOPs = []

  unit_op_table_header = ["Sample name", "UnitOP", "Arm&Clamp Time", "Reactor Time", "Sonicator time", "Centrifuge time"] 

  #Example
  Add_fluids_op =      ["Some_sample_name", "Add_fluids",       3,  0, 0,  0]
  Take_picture_op =    ["Some_sample_name", "Take_picture",     2,  0, 0,  0]
  Start_reaction_op =  ["Some_sample_name", "Start_reaction", 0.5, 20, 0,  0]
  Centrifuge_op =      ["Some_sample_name", "Centrifuge_op",  0.5,  0, 0, 10]
  Remove_supernatent = ["Some_sample_name", "Centrifuge_op",    3,  0, 0,  0]
  Sonicate_pellet =    ["Some_sample_name", "Centrifuge_op",  0.5,  0, 5,  0]
  
  Add_fluids_op =      ["Othersample_name", "Add_fluids",       3,  0, 0,  0]
  Take_picture_op =    ["Othersample_name", "Take_picture",     2,  0, 0,  0]
  Start_reaction_op =  ["Othersample_name", "Start_reaction", 0.5, 50, 0,  0]
  Centrifuge_op =      ["Othersample_name", "Centrifuge_op",  0.5,  0, 0, 10]
  Remove_supernatent = ["Othersample_name", "Centrifuge_op",    3,  0, 0,  0]
  Sonicate_pellet =    ["Othersample_name", "Centrifuge_op",  0.5,  0, 5,  0]

  #Rules:
  # for each sample, unit ops must be done in this order ["Add_fluids", "Start_reaction", "Centrifuge_op", "Remove_supernatent"]
  # Arm&Clamp time must happen sequentially
  # Reactor time can be in parallel up to 8 heater blocks, 4 spots each,
  #   but all samples in a reactor must finish at the same time. 
  # Centrifuge time can be in parallel with other ops
  # Sonicator time can be in parallel with other ops 
  
  #Goal:
  # find the order of operations that satisfies all the conditions, with the min total time. 







def Execute_UnitOp(Sample_ID, UnitOP, c, system_db, experiment):
  """A generaric to execute any unit operation"""

  #Check if anything in gripper
  gripper_occupied = full_gripper_available_check(experiment.sample_db, system_db)

  if gripper_occupied == True:
    #Get that sample id
    sample_in_gripper = "X123" #TODO read sample db for adress [2 0 0]

    if Sample_ID != sample_in_gripper:
      #If the sample in the gripper is NOT the one we want
      #Then set it aside in the vial rack

      #TODO find open spot in vial rack
      set_asside_dest = [1, 0, 12]#TODO read system db for open spots in vial rack
      Move_Sample(sample_in_gripper, set_asside_dest, experiment.sample_db, system_db, c)



  if UnitOP == "Add_fluids":
    #TODO: if the centrifuge or sonicator is in use, pause those
    Add_fluids(Sample_ID, c, system_db, experiment)
    #TODO: if the centrifuge or sonicator was in use, re-start those

  if UnitOP == "Take_picture":
    Take_picture(Sample_ID, c, system_db, experiment)

  if UnitOP == "Start_reaction":

    Start_reaction(Sample_ID, c, system_db, experiment)