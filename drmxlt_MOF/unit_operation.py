import time
import numpy as np

from drmxlt_MOF.moving_vials import Violent_Action_Precheck, assign_sample_to_vial, Premove_Check_, Move_Sample
from drmxlt_MOF.fluid_dispensing import Fluid_dispense
from drmxlt_MOF.dummy_c9 import tare_balance


def Add_fluids(Sample_ID, c, system_db, experiment, new_sample= True):


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
  for key in fluid_assignments:
    fluid = key
    exp_vol = fluid_assignments[key]
    Fluid_dispense(fluid, exp_vol, destination, c, experiment.fluid_db)
    weighed_composition[fluid] = c.read_steady_scale() 

  experiment.sample_db[Sample_ID]["Weighed Composition (g)"] = weighed_composition

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






