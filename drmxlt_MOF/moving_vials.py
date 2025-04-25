import numpy as np

# from drmxlt_MOF.Binary_reaction.sample_db_setup import find_address
# from drmxlt_MOF.Locator import *
from Locator import *
#TODO move reactor locations to Locator.py from Locator_supplemental.py
from drmxlt_MOF.Locator_supplemental import reactor_0, reactor_1, reactor_2, reactor_3, reactor_4, reactor_5, reactor_6, reactor_7




#Initial Assignment of sample to a vial
def assign_sample_to_vial(Sample_ID, sample_db, system_db):
  current_address = sample_db[Sample_ID]["Address"]

  #If the current address starts [0, 0, _] then it's a new sample
  new_sample = all(current_address[0:2] == np.array([0, 0]))

  if new_sample:
    #Try to assign to left rack
    mask = system_db["left_rack_assignments"] == "Unassigned"

    #If there are any available vials
    if mask.any():
      vial_id = np.min(system_db["vial_rack_left_array"][mask])
      address = np.array([1, 0, vial_id])
      sample_db[Sample_ID]["Address"] = address #update the sample database with new address
      vial_mask = system_db["vial_rack_left_array"] == vial_id
      system_db["left_rack_assignments"][vial_mask] = Sample_ID #update the system database with new assignment


    else:
      #Try to assign to right rack
      mask = system_db["right_rack_assignments"] == "Unassigned"
      if mask.any():
        vial_id = np.min(system_db["vial_rack_right_array"][mask])
        address = [1, 1, vial_id]
        sample_db[Sample_ID]["Address"] = address #update the sample database with new address
        vial_mask = system_db["vial_rack_right_array"] == vial_id
        system_db["right_rack_assignments"][vial_mask] = Sample_ID #update the system database with new assignment

      else:
        raise Exception("No available vials")

  else:
    raise Exception(f"Sample {Sample_ID} already assigned {current_address}")
  

def find_open_vial_rack_addresses(system_db):
  loaded_rack_left = system_db["loaded_rack_left"]
  loaded_left_mask = np.array(loaded_rack_left == 0)
  left_rack_assignments = system_db["left_rack_assignments"]
  left_assignment_mask = np.array(left_rack_assignments == "Empty")

  left_truth_test = loaded_left_mask == left_assignment_mask
  if not left_truth_test.all():
    raise Exception("System Database vial rack loading and assignments out of sync")
  
  if left_assignment_mask.any():
    #Find all the free positions in the left rack
    free_left_positions = system_db['vial_rack_left_array'][left_assignment_mask].reshape(-1,1)

    free_rack1 = np.ones_like(free_left_positions) #Zipcode 1, _, _ for vial racks
    free_left_rack = np.zeros_like(free_left_positions)# Zipcode 1, 0, _ for left vial rack

    #Concatentate for all the zipcodes in the left rack
    free_left_addresses = np.concatenate((free_rack1, free_left_rack, free_left_positions), axis = 1)

  else:
    free_left_addresses = np.empty((0,3))

  loaded_rack_right = system_db["loaded_rack_right"]
  loaded_right_mask = loaded_rack_right == 0
  right_rack_assignments = system_db["right_rack_assignments"]
  right_assignment_mask = right_rack_assignments == "Empty"

  right_truth_test = loaded_right_mask == right_assignment_mask
  if not right_truth_test.all():
    raise Exception("System Database vial rack loading and assignments out of sync")
  
  if right_assignment_mask.any():
    #Find all the free positions in the right rack
    free_right_positions = system_db['vial_rack_right_array'][right_assignment_mask].reshape(-1,1)

    free_rack2 = np.ones_like(free_right_positions) #Zipcode 1, _, _ for vial racks
    free_right_rack = np.zeros_like(free_right_positions)# Zipcode 1, 0, _ for right vial rack

    #Concatentate for all the zipcodes in the right rack
    free_right_addresses = np.concatenate((free_rack2, free_right_rack, free_right_positions), axis = 1)

  else:
    free_right_addresses = np.empty((0,3))

  #Concatenate the free addresses from both racks
  free_addresses = np.concatenate((free_left_addresses, free_right_addresses), axis = 0).astype(int)

  return free_addresses



# Status checking
def check_samples_in_gripper(sample_db):
  top_level_addresses = []
  for key in sample_db.keys():
    address = sample_db[key]["Address"]
    top_level_addresses.append(address[0])
  top_level_addresses = np.array(top_level_addresses)

  any_in_gripper = any(top_level_addresses == 2)

  return any_in_gripper

def system_using_gripper(system_db):
  gripper_occupied = system_db["gripper_occupied"]
  return gripper_occupied

def full_gripper_available_check(sample_db, system_db):
  any_in_gripper = check_samples_in_gripper(sample_db)
  gripper_occupied = system_using_gripper(system_db)

  test1 = any_in_gripper == False
  test2 = gripper_occupied == False

  gripper_available = test1 and test2

  return gripper_available

def Violent_Action_Precheck(c):
#   #Is the sonicator on?
#   sonicator_status = c.sonicator
# 
#   #Is the centrifuge on?
#   centrifuge_status = c.centrifuge
# 
#   violent_action = sonicator_status or centrifuge_status
  
  
  violent_action = False
  return violent_action


#Pre Move checking to make sure the move is possible at this time:
def Premove_Check_(Sample_ID, destination, sample_db, system_db, c, hot_load_temperature_threshold = 1000.0):
  source = sample_db[Sample_ID]["Address"]

  if all(source == destination): #If the sample is already there, do nothing
    return True

  #Check that the gripper is available (if not move whatever is in the gripper to the rack?)
  test = full_gripper_available_check(sample_db, system_db)
  if test == False:
    raise Exception("Gripper is not available") #TODO replace with wait to allow for parallel sample handling



  #Check source readiness
  if source[0] == 1: #If sample is in the vial rack
    None

  if source[0] == 2: #If sample is in the gripper
    None

  if source[0] == 3: # If sample is in the clamp
    clamp_open = system_db["clamp_status"]
    if clamp_open == "Closed": #if the clamp is closed, open it.
      c.open_clamp()
      system_db["clamp_status"] = "Open"


  if source[0] == 4: # if sample is in a reactor
    #check if reactor hat is off
    hat = system_db['reactor'][source[1]]["Hat Status"]
    test1 = hat == "Off"
    #TODO take the hat off
    #TODO each position has an indepenedent hat

    #check if the tempearture is low enough

    temp = system_db['reactor'][source[1]]["Temperature (C)"]
    test2 = temp < hot_load_temperature_threshold

    reactor_ready = test1 and test2

    if reactor_ready == False:
      raise Exception("reactor is not ready")

  #Check destination readiness
  if destination[0] == 1: #If destination is in the vial rack
    #read the occupancy of the vial rack and position

    if destination[1] == 0: #If destination is in the left rack
      vial_rack_array = system_db["vial_rack_left_array"]
      mask = vial_rack_array == destination[2] #mask to that address

      #Is that address marked as loaded?
      vial_loaded = system_db["loaded_rack_left"][mask]
      test1 = vial_loaded == 0
      #Is there something assigned to that address <--- should be a redundent test
      vial_assigned = system_db["left_rack_assignments"][mask]
      test2 = vial_assigned == "Empty"

      rack_ready = test1 and test2
      if rack_ready == False:
        raise Exception(f"Rack occupied with {vial_assigned}")

    elif destination[1] == 1: #If destination is in the right rack
      vial_rack_array = system_db["vial_rack_right_array"]
      mask = vial_rack_array == destination[2] #mask to that address

      #Is that address marked as loaded?
      vial_loaded = system_db["loaded_rack_right"][mask]
      test1 = vial_loaded == 0
      #Is there something assigned to that address <--- should be a redundent test
      vial_assigned = system_db["right_rack_assignments"][mask]
      test2 = vial_assigned == "Empty"

      rack_ready = test1 and test2
      if rack_ready == False:
        raise Exception(f"Rack occupied with {vial_assigned}")

    else:
      raise Exception("Invalid rack location")


  if destination[0] == 2: #If destination is in the gripper
    #TODO check if gripper is occupied
    gripper_occupied = system_db["gripper_occupied"]
    #TODO get the name of the thing in the gripper
    #TODO find an available zip code in the vial rack
    # if gripper_occupied == True:
    #   Move_Sample(some_sample, some_vial_zip_code)
    # pass

  if destination[0] == 3: #If destination is in the clamp
    #check if clamp is occupied
    clamp_occupied = system_db["clamp_assignment"]
    if clamp_occupied != "Empty":
      raise Exception(f"Clamp occupied with {clamp_occupied}")

    clamp_open = system_db["clamp_status"]
    if clamp_open == "Closed": #if the clamp is closed, open it.
      c.open_clamp()
      system_db["clamp_status"] = "Open"

  if destination[0] == 4: #If destination is in a reactor
    #check if reactor hat is off
    hat = system_db['reactor'][destination[1]]["Hat Status"]
    test1 = hat == "Off"

    #check if the tempearture is low enough
    temp = system_db['reactor'][destination[1]]["Temperature"]
    test2 = temp < hot_load_temperature_threshold 

    reactor_ready = test1 and test2

    if reactor_ready == False:
      raise Exception("reactor is not ready")

    #check if position is occupied
    occupancy = system_db["reactor"][destination[1]][destination[2]]["Assignment"]
    if occupancy != "Empty":
      raise Exception(f"reactor is occupied with {occupancy}")

  if destination[0] == 5: #If destination is the syringe pumps
    raise Exception("Syringe pumps not a valid destination for a sample")

  return True


def Move_Sample(Sample_ID, destination, sample_db, system_db, c):
  source = sample_db[Sample_ID]["Address"]

  #### Source #####
  if source[0] == 1: #If sample is in the vial rack
    if source[1] == 0: #If sample is in the left vial rack
      c.goto_safe(rack_left[source[2]])
      c.close_gripper()
      system_db['gripper_status'] = "Closed"
      system_db["gripper_occupied"] = True
      sample_db[Sample_ID]["Address"] = np.array([2, 0, 0]) #tell sample_db that it's in the gripper
      mask = system_db["vial_rack_left_array"] == source[2]
      system_db["loaded_rack_left"][mask] = 0 #Tell the system_db that this position is not loaded
      system_db["left_rack_assignments"][mask] = "Empty" #Tell the system_db that this position is empty


    elif source[1] == 1: #If sample is in the right vial rack
      c.goto_safe(rack_right[source[2]])
      c.close_gripper()
      system_db['gripper_status'] = "Closed"
      system_db["gripper_occupied"] = True
      sample_db[Sample_ID]["Address"] = np.array([2, 0, 0]) #tell sample_db that it's in the gripper
      mask = system_db["vial_rack_right_array"] == source[2]
      system_db["loaded_rack_right"][mask] = 0 #Tell the system_db that this position is not loaded
      system_db["right_rack_assignments"][mask] = "Empty" #Tell the system_db that this position is empty

    else:
      raise Exception("Invalid rack location")

  if source[0] == 2: #If sample is in the gripper
    pass

  if source[0] == 3: #If sample is in the clamp
    c.goto_safe(vclamp)
    c.close_gripper()
    system_db['gripper_status'] = "Closed"
    system_db["gripper_occupied"] = True
    sample_db[Sample_ID]["Address"] = np.array([2, 0, 0]) #tell sample_db that it's in the gripper
    system_db["clamp_assignment"] = "Empty" #Tell the system_db that the clamp is now empty

  if source[0] == 4: #If sample is in a reactor
    if source[1] == 0: #If sample is in reactor 0
      c.goto_safe(reactor_0[source[2]])
      # c.goto_safe(react0[source[2]])
      c.close_gripper()
      system_db['gripper_status'] = "Closed"
      system_db["gripper_occupied"] = True
      sample_db[Sample_ID]["Address"] = np.array([2, 0, 0]) #tell sample_db that it's in the gripper
      

    elif source[1] == 1: #If sample is in reactor 1
      # c.goto_safe(reactor_1[source[2]])
      c.goto_safe(react1[source[2]])
      c.close_gripper()
      system_db['gripper_status'] = "Closed"
      system_db["gripper_occupied"] = True
      sample_db[Sample_ID]["Address"] = np.array([2, 0, 0]) #tell sample_db that it's in the gripper

    elif source[1] == 2: #If sample is in reactor 2
      c.goto_safe(reactor_2[source[2]])
      # c.goto_safe(react2[source[2]])
      c.close_gripper()
      system_db['gripper_status'] = "Closed"
      system_db["gripper_occupied"] = True
      sample_db[Sample_ID]["Address"] = np.array([2, 0, 0]) #tell sample_db that it's in the gripper

    elif source[1] == 3: #If sample is in reactor 3
      c.goto_safe(reactor_3[source[2]])
      # c.goto_safe(react3[source[2]])
      c.close_gripper()
      system_db['gripper_status'] = "Closed"
      system_db["gripper_occupied"] = True
      sample_db[Sample_ID]["Address"] = np.array([2, 0, 0]) #tell sample_db that it's in the gripper

    elif source[1] == 4: #If sample is in reactor 4
      c.goto_safe(reactor_4[source[2]])
      # c.goto_safe(react4[source[2]])
      c.close_gripper()
      system_db['gripper_status'] = "Closed"
      system_db["gripper_occupied"] = True
      sample_db[Sample_ID]["Address"] = np.array([2, 0, 0]) #tell sample_db that it's in the gripper

    elif source[1] == 5: #If sample is in reactor 5
      c.goto_safe(reactor_5[source[2]])
      # c.goto_safe(react5[source[2]])
      c.close_gripper()
      system_db['gripper_status'] = "Closed"
      system_db["gripper_occupied"] = True
      sample_db[Sample_ID]["Address"] = np.array([2, 0, 0]) #tell sample_db that it's in the gripper

    elif source[1] == 6: #If sample is in reactor 6
      c.goto_safe(reactor_6[source[2]])
      # c.goto_safe(react6[source[2]])
      c.close_gripper()
      system_db['gripper_status'] = "Closed"
      system_db["gripper_occupied"] = True
      sample_db[Sample_ID]["Address"] = np.array([2, 0, 0]) #tell sample_db that it's in the gripper

    elif source[1] == 7: #If sample is in reactor 7
      c.goto_safe(reactor_7[source[2]])
      # c.goto_safe(react7[source[2]])
      c.close_gripper()
      system_db['gripper_status'] = "Closed"
      system_db["gripper_occupied"] = True
      sample_db[Sample_ID]["Address"] = np.array([2, 0, 0]) #tell sample_db that it's in the gripper

    else:
      raise Exception("Invalid reactor location")
    system_db["reactor"][source[1]][source[2]]["Assignment"] = "Empty" #Tell the system_db that this reactor location is empty

  if destination[0] == 5: #If destination is the syringe pumps
    raise Exception("Syringe pumps not a valid source location for a sample")
  
  #TODO: push sample db to Cordra

  #### Destination #####

  if destination[0] == 1: #If destination is in the vial rack
    if destination[1] == 0: #If destination is in the left vial rack
      c.goto_safe(rack_left[destination[2]])
      c.open_gripper()
      system_db['gripper_status'] = "Open"
      system_db["gripper_occupied"] = False
      sample_db[Sample_ID]["Address"] = np.array([1, 0, destination[2]]) #tell sample_db that it's in the vial rack
      mask = system_db["vial_rack_left_array"] == source[2]
      system_db["loaded_rack_left"][mask] = 1 #Tell the system_db that this position is now loaded
      system_db["left_rack_assignments"][mask] = Sample_ID #Tell the system_db that this position now has the sample

    elif destination[1] == 1: #If destination is in the right vial rack
      c.goto_safe(rack_right[destination[2]])
      c.open_gripper()
      system_db['gripper_status'] = "Open"
      system_db["gripper_occupied"] = False
      sample_db[Sample_ID]["Address"] = np.array([1, 1, destination[2]]) #tell sample_db that it's in the vial rack
      mask = system_db["vial_rack_right_array"] == source[2]
      system_db["loaded_rack_right"][mask] = 1 #Tell the system_db that this position is now loaded
      system_db["right_rack_assignments"][mask] = Sample_ID #Tell the system_db that this position now has the sample

    else:
      raise Exception("Invalid rack location")

  if destination[0] == 2: #If destination is in the gripper
    c.close_gripper()
    system_db['gripper_status'] = "Closed"
    system_db["gripper_occupied"] = True
    sample_db[Sample_ID]["Address"] = np.array([2, 0, 0]) #tell sample_db that it's in the gripper

  if destination[0] == 3: #If destination is in the clamp
    c.goto_safe(vclamp)
    c.open_gripper()
    system_db['gripper_status'] = "Open"
    system_db["gripper_occupied"] = False
    sample_db[Sample_ID]["Address"] = np.array([3, 0, 0]) #tell sample_db that it's in the clamp
    system_db["clamp_assignment"] = Sample_ID #Tell the system_db that the clamp is now has the sample

  if destination[0] == 4: #If destination is in a reactor
    if destination[1] == 0: #If destination is reactor 0
      c.goto_safe(reactor_0[destination[2]])
      # c.goto_safe(react0[destination[2]])
      c.open_gripper()
      system_db['gripper_status'] = "Open"
      system_db["gripper_occupied"] = False
      sample_db[Sample_ID]["Address"] = np.array([4, 0, destination[2]]) #tell sample_db that it's in the reactor

    elif destination[1] == 1: #If destination is reactor 1
      # c.goto_safe(reactor_1[destination[2]])
      c.goto_safe(react1[destination[2]])
      c.open_gripper()
      system_db['gripper_status'] = "Open"
      system_db["gripper_occupied"] = False
      sample_db[Sample_ID]["Address"] = np.array([4, 1, destination[2]]) #tell sample_db that it's in the reactor

    elif destination[1] == 2: #If destination is reactor 2
      c.goto_safe(reactor_2[destination[2]])
      # c.goto_safe(react2[destination[2]])
      c.open_gripper()
      system_db['gripper_status'] = "Open"
      system_db["gripper_occupied"] = False
      sample_db[Sample_ID]["Address"] = np.array([4, 2, destination[2]]) #tell sample_db that it's in the reactor

    elif destination[1] == 3: #If destination is reactor 3
      c.goto_safe(reactor_3[destination[2]])
      # c.goto_safe(react3[destination[2]])
      c.open_gripper()
      system_db['gripper_status'] = "Open"
      system_db["gripper_occupied"] = False
      sample_db[Sample_ID]["Address"] = np.array([4, 3, destination[2]]) #tell sample_db that it's in the reactor

    elif destination[1] == 4: #If destination is reactor 4
      c.goto_safe(reactor_4[destination[2]])
      # c.goto_safe(react4[destination[2]])
      c.open_gripper()
      system_db['gripper_status'] = "Open"
      system_db["gripper_occupied"] = False
      sample_db[Sample_ID]["Address"] = np.array([4, 4, destination[2]]) #tell sample_db that it's in the reactor

    elif destination[1] == 5: #If destination is reactor 5
      c.goto_safe(reactor_5[destination[2]])
      # c.goto_safe(react5[destination[2]])
      c.open_gripper()
      system_db['gripper_status'] = "Open"
      system_db["gripper_occupied"] = False
      sample_db[Sample_ID]["Address"] = np.array([4, 5, destination[2]]) #tell sample_db that it's in the reactor

    elif destination[1] == 6: #If destination is reactor 6
      c.goto_safe(reactor_6[destination[2]])
      # c.goto_safe(react6[destination[2]])
      c.open_gripper()
      system_db['gripper_status'] = "Open"
      system_db["gripper_occupied"] = False
      sample_db[Sample_ID]["Address"] = np.array([4, 6, destination[2]]) #tell sample_db that it's in the reactor

    elif destination[1] == 7: #If destination is reactor 7
      c.goto_safe(reactor_7[destination[2]])
      # c.goto_safe(react7[destination[2]])
      c.open_gripper()
      system_db['gripper_status'] = "Open"
      system_db["gripper_occupied"] = False
      sample_db[Sample_ID]["Address"] = np.array([4, 7, destination[2]]) #tell sample_db that it's in the reactor

    else:
      raise Exception("Invalid reactor location")
    system_db["reactor"][destination[1]][destination[2]]["Assignment"] = Sample_ID #Tell the system_db that this reactor now has the sample

  if destination[0] == 5: #If destination is the syringe pumps
    raise Exception("Syringe pumps not a valid destination for a sample")
  
  #TODO: push sample db to Cordra


def force_Move_Vial(source, destination, c):
  """WARNING: untracked vial movement
  This function will attempt to move a vial from any 
  valid source location to any valid destination location
  WITHOUT checking the system or sample databases
  WITHOUT updtaing the system or sample databases
  WITHOUT checking for occupancy conflicts

  Useful primiarily for seting up the system outside of normal experiment operations.   
  """
  #### Source #####
  if source[0] == 1: #If sample is in the vial rack
    if source[1] == 0: #If sample is in the left vial rack
      c.goto_safe(rack_left[source[2]])
      c.close_gripper()

    elif source[1] == 1: #If sample is in the right vial rack
      c.goto_safe(rack_right[source[2]])
      c.close_gripper()

    else:
      raise Exception("Invalid rack location")

  if source[0] == 2: #If sample is in the gripper
    pass

  if source[0] == 3: #If sample is in the clamp
    c.goto_safe(vclamp)
    c.close_gripper()
   
  if source[0] == 4: #If sample is in a reactor
    if source[1] == 0: #If sample is in reactor 0
      c.goto_safe(reactor_0[source[2]])
      c.close_gripper()    

    elif source[1] == 1: #If sample is in reactor 1
      c.goto_safe(reactor_1[source[2]])
      c.close_gripper()

    elif source[1] == 2: #If sample is in reactor 2
      c.goto_safe(reactor_2[source[2]])
      c.close_gripper()

    elif source[1] == 3: #If sample is in reactor 3
      c.goto_safe(reactor_3[source[2]])
      c.close_gripper()

    elif source[1] == 4: #If sample is in reactor 4
      c.goto_safe(reactor_4[source[2]])
      c.close_gripper()

    elif source[1] == 5: #If sample is in reactor 5
      c.goto_safe(reactor_5[source[2]])
      c.close_gripper()

    elif source[1] == 6: #If sample is in reactor 6
      c.goto_safe(reactor_6[source[2]])
      c.close_gripper()

    elif source[1] == 7: #If sample is in reactor 7
      c.goto_safe(reactor_7[source[2]])
      c.close_gripper()

    else:
      raise Exception("Invalid reactor location")
    system_db["reactor"][source[1]][source[2]]["Assignment"] = "Empty" #Tell the system_db that this reactor location is empty

  if destination[0] == 5: #If destination is the syringe pumps
    raise Exception("Syringe pumps not a valid source location for a sample")
  
  #TODO: push sample db to Cordra

  #### Destination #####

  if destination[0] == 1: #If destination is in the vial rack
    if destination[1] == 0: #If destination is in the left vial rack
      c.goto_safe(rack_left[destination[2]])
      c.open_gripper()

    elif destination[1] == 1: #If destination is in the right vial rack
      c.goto_safe(rack_right[destination[2]])
      c.open_gripper()

    else:
      raise Exception("Invalid rack location")

  if destination[0] == 2: #If destination is in the gripper
    c.close_gripper()

  if destination[0] == 3: #If destination is in the clamp
    c.goto_safe(vclamp)
    c.open_gripper()


  if destination[0] == 4: #If destination is in a reactor
    if destination[1] == 0: #If destination is reactor 0
      c.goto_safe(reactor_0[destination[2]])
      c.open_gripper()

    elif destination[1] == 1: #If destination is reactor 1
      c.goto_safe(reactor_1[destination[2]])
      c.open_gripper()

    elif destination[1] == 2: #If destination is reactor 2
      c.goto_safe(reactor_2[destination[2]])
      c.open_gripper()

    elif destination[1] == 3: #If destination is reactor 3
      c.goto_safe(reactor_3[destination[2]])
      c.open_gripper()

    elif destination[1] == 4: #If destination is reactor 4
      c.goto_safe(reactor_4[destination[2]])
      c.open_gripper()

    elif destination[1] == 5: #If destination is reactor 5
      c.goto_safe(reactor_5[destination[2]])
      c.open_gripper()

    elif destination[1] == 6: #If destination is reactor 6
      c.goto_safe(reactor_6[destination[2]])
      c.open_gripper()

    else:
      raise Exception("Invalid reactor location")
    system_db["reactor"][destination[1]][destination[2]]["Assignment"] = Sample_ID #Tell the system_db that this reactor now has the sample

  if destination[0] == 5: #If destination is the syringe pumps
    raise Exception("Syringe pumps not a valid destination for a sample")
  
  #TODO: push sample db to Cordra