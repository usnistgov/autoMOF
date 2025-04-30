import numpy as np
import pandas as pd

import collections
from ortools.sat.python import cp_model


#TODO encode some logic for the case where there are more reactions at the same temperature than there are positions in the same reactor!!!

def reactor_use_assignment(reactor_df, number_of_reactors, positions_in_reactor):
  """This function reads the reactor dataframe
  and if there are more reactors needed than are available,
  merge the shortest durations to the same reactor (to happen sequentially). 
  
  Keep doing that until the reactor dataframe uses at most the same number as available reactors. 
  """ 


  #Sort so the longest reactor use is first
  reactor_df = reactor_df.sort_values("Total Reactor Duration (Ds)", ascending = False)

  #Get array of how which reactors are needed
  reactors_required = np.arange(len(reactor_df))

  reactor_df['Reactor'] = reactors_required # re-assign the reactor index order

  #If there are more required reactors than the total number, then merge the ones with the sortest duration
  if np.max(reactors_required) >= number_of_reactors:
    second_to_last_duration = reactor_df["Total Reactor Duration (Ds)"].to_numpy()[-2]
    second_to_last_index = reactor_df[reactor_df["Total Reactor Duration (Ds)"] == second_to_last_duration].index[0]


    last_duration = reactor_df["Total Reactor Duration (Ds)"].to_numpy()[-1]
    last_index = reactor_df[reactor_df["Total Reactor Duration (Ds)"] == last_duration].index[0]

    #Pair the last 2 rows together:
    use1 = reactor_df.iloc[-1]["Reactor Use (Ds)"]
    temp1 = reactor_df.iloc[-1]["Reactor Temperature (C)"]
    use2 = reactor_df.iloc[-2]["Reactor Use (Ds)"]
    temp2 = reactor_df.iloc[-2]["Reactor Temperature (C)"]

    # total_duration = np.sum([use1, use2])
    total_duration = np.sum(use1 + use2)
    total_use = use1 + use2
    total_temp = temp1 + temp2

    #overwrite second to last row with new values
    reactor_df.at[second_to_last_index, "Reactor Use (Ds)"] = total_use
    reactor_df.at[second_to_last_index, "Reactor Temperature (C)"] = total_temp
    reactor_df.at[second_to_last_index, "Total Reactor Duration (Ds)"] = total_duration

    #drop the last row
    reactor_df = reactor_df.drop(last_index)


    #Run again
    reactor_df = reactor_use_assignment(reactor_df, number_of_reactors, positions_in_reactor)

  return reactor_df


def assign_reactors(unit_ops_df, number_of_reactors, positions_in_reactor):
  """Read the unit operations dataframe and assign reactor IDs to each react operation

  Reactions at the same temperature should be on the same reactor (unless this is more than can fit).
  Reactors can be re-used for several groups of reactions 
  Shortest durations of groups of reactions get merged to the same reactor. 
  Until all of the react unit operations are assigned to one of the available reactors. 
  """

  #Get array of all the unique temperatures
  unique_temperatures = np.unique(unit_ops_df[unit_ops_df["UnitOP"]=='react']["Reactor Temperature (C)"])
  #Make a list of names of reactors for each unique temperature
  reactors_required = np.arange(len(unique_temperatures))

  #Create a list object of those temperatures
  unique_temperatures
  list_of_temperatures = []
  for temp in unique_temperatures:
    list_of_temperatures.append([temp])


  total_react_duration = []
  #for each unique temperature, pick the longer reactor duration
  for temp in unique_temperatures:
    temp_mask = unit_ops_df[unit_ops_df["UnitOP"]=='react']["Reactor Temperature (C)"] == temp
    total_react_duration.append(np.max(unit_ops_df[unit_ops_df["UnitOP"]=='react'][temp_mask]["Duration (Ds)"]))
  total_react_duration = np.array(total_react_duration)

  #Create a list object of those reaction durations
  list_of_react_durations = []
  for duration in total_react_duration:
    list_of_react_durations.append([duration])

  #Initiallize a reaction dataframe
  reactor_df = pd.DataFrame()
  reactor_df["Reactor"] = reactors_required
  reactor_df["Total Reactor Duration (Ds)"] = total_react_duration
  reactor_df["Reactor Use (Ds)"] = list_of_react_durations #Needs to be a list
  reactor_df["Reactor Temperature (C)"] = list_of_temperatures #Needs to be a list

  #Convert the list objects to "objects" - allows for re-assigning these cells with a new list
  reactor_df['Reactor Use (Ds)'] = reactor_df['Reactor Use (Ds)'].astype("object")
  reactor_df['Reactor Temperature (C)'] = reactor_df['Reactor Temperature (C)'].astype("object")



  #Configure the reactor use
  reactor_df = reactor_use_assignment(reactor_df, number_of_reactors, positions_in_reactor)


  #Assign reactors in the unit ops dataframe using the reactor dataframe

  #Create a new index column (rather than the concatenated one that cycled through each op for each sample)
  unit_ops_df = unit_ops_df.reset_index()
  #Rename the old index colum to be the order of operations for each sample
  unit_ops_df = unit_ops_df.rename(columns = {"index": "Op Order"})

  #Get index of react ops
  list_of_react_ops = unit_ops_df.index[unit_ops_df["UnitOP"] == 'react'].tolist()

  #For each of those indexes
  for i in list_of_react_ops:
    #Get the reaction temperature
    temperature = unit_ops_df.loc[i, "Reactor Temperature (C)"]

    #For each possible reactor
    for reactor in range(number_of_reactors):
      #Read the reactor datafram of that reactor
      sub_df = reactor_df[reactor_df["Reactor"] == reactor]

      #Get the list of temperatures of that reactor
      temps = list(sub_df["Reactor Temperature (C)"])[0]

      #If the reaction temperature is in the list of temperatures for that reactor
      if temperature in temps:
        #Assign that reactor
        unit_ops_df.at[i, "Reactor"] = reactor


  return unit_ops_df, reactor_df


def define_machine_IDs(reactors, centrifuge = 1, sonicator = 1):
  machine_id = ["Arm&Clamp"]
  
  for i in range(reactors):
    machine_id.append(f"Reactor {i}")

  for i in range(centrifuge):   
    machine_id.append(f"Centrifuge {i}")

  for i in range(sonicator):   
    machine_id.append(f"Sonicator {i}")

  machines_count = len(machine_id)
  all_machines = range(machines_count)  

  return machine_id, machines_count, all_machines


def create_unit_ops_df(sample_db, 
                       Add_fluids = True, 
                       React = True,
                       Centrifuge = True,
                       Remove_supernatent = True,
                       Sonicate = True):

    """Function for creating a DataFrame of the Unit Ops and sub_unit ops
    for each sample. Uses hard-coded durations for the Arm&Clamp movements

    Durations are in Ds - so that there is fine enough fidelity, but still an integer (as needed for constraint solver)
    
    Which unit ops are performed and added to the dataframe is controled by the boolean flags."""


    header = ["Sample Name", "UnitOP", "Duration (Ds)", "Reactor", "Reactor Temperature (C)"]
    unit_ops_df = pd.DataFrame(columns = header)
    for key in sample_db.keys():
        
        if Add_fluids == True:
            sub_df = pd.DataFrame([[key, "add_fluids", 3*6, None, 0]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])

        if React == True:
            sub_df = pd.DataFrame([[key, "move_to_reactor", 0.5*6, None, 0]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])

            temp = sample_db[key]["Temperature (C)"] 
            time = sample_db[key]["Reaction Time (min)"] 

            sub_df = pd.DataFrame([[key, "react", time*6, None, temp]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])

        if Centrifuge == True:
            sub_df = pd.DataFrame([[key, "move_to_centrifuge", 0.5*6, None, 0]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])

            sub_df = pd.DataFrame([[key, "centrifuge", 10*6, None, 0]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])

        if Remove_supernatent == True:
            sub_df = pd.DataFrame([[key, "rm_supernatent", 3*6, None, 0]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])
        
        if Sonicate == True:
            sub_df = pd.DataFrame([[key, "move_to_sonicator", 0.5*6, None, 0]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])

            sub_df = pd.DataFrame([[key, "sonicate", 5*6, None, 0]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])

    return unit_ops_df

def define_cp_job(unit_ops_df,
                  reactors, 
                  centrifuge = 1, 
                  sonicator = 1):

    """Function that reads the unit_ops_df,
    and creates a constraint satisfaction problem.
    Specifically a job shop problem. 
    The components of the robot are modeled as different "machines"

    Contraints:
    For each sample the operations must happen in order (add_fluids is before react, etc.)
    The arm&clamp can only handle 1 sample at a time
    Reactions that overlap on the same reactor must END at the same time. 

    """


    #Start a container for all the jobs (a job is the collectons of each task for a sample)
    job_list = []

    #Initialize the model
    model = cp_model.CpModel()

    #Enumerate and name all the "machines"
    machine_id, machines_count, all_machines = define_machine_IDs(reactors, centrifuge, sonicator)

    #Calculate the total time horizon
    horizon = int(np.ceil(np.sum(unit_ops_df["Duration (Ds)"].to_numpy())))
    print(f"Horizon = {horizon}")

    # Named tuple to store information about created variables.
    task_type = collections.namedtuple("task_type", "start end interval")
    # Named tuple to manipulate solution information.
    assigned_task_type = collections.namedtuple("assigned_task_type", "start job index duration")

    # Creates job intervals and add to the corresponding machine lists.
    all_tasks = {}
    machine_to_intervals = collections.defaultdict(list)


    #Get all the sample names from the unit ops df
    sample_names = np.unique(unit_ops_df["Sample Name"].to_numpy())

    for job_id, sample_name in enumerate(sample_names):
        #Get all the unit ops for that sample
        sub_df = unit_ops_df[unit_ops_df["Sample Name"] == sample_name]

        # #Order this dataframe by the Op order
        # sub_df = sub_df.sort_values("Op Order")

        #start a container for the tasks
        task_list = []
        for task_df in sub_df.iterrows():

            operation = task_df[1]["UnitOP"]
            # task_id = task_df[1]["Op Order"]
            # print(task_id)

            if operation == "add_fluids":
                task_id = 0
                task = (0, int(np.ceil(task_df[1]["Duration (Ds)"]))) #Add_fluids only uses the arm&clamp
                task_list.append(task)

                machine, duration = task #Unpack the tuple
                suffix = f"_{job_id}_{task_id}" #Create suffics for the variables
                start_var = model.new_int_var(0, horizon, "start" + suffix) #Start of this task can be anywhere between 0 and horizon
                end_var = model.new_int_var(0, horizon, "end" + suffix) #End of this task can be anywhere between 0 and horizon
                interval_var = model.new_interval_var(start_var, duration, end_var, "interval" + suffix) #Model the interval between start and end
                all_tasks[job_id, task_id] = task_type(start=start_var, end=end_var, interval=interval_var) #Add this task to dictionary of all tasks
                machine_to_intervals[machine].append(interval_var) #Add the interval to the list of tasks for this machine

            elif operation == "move_to_reactor":
                task_id = 1
                task = (0, int(np.ceil(task_df[1]["Duration (Ds)"]))) #use the arm&clamp to move the sample to the reactor
                task_list.append(task)

                machine, duration = task #Unpack the tuple
                suffix = f"_{job_id}_{task_id}" #Create suffics for the variables
                start_var = model.new_int_var(0, horizon, "start" + suffix) #Start of this task can be anywhere between 0 and horizon
                end_var = model.new_int_var(0, horizon, "end" + suffix) #End of this task can be anywhere between 0 and horizon
                interval_var = model.new_interval_var(start_var, duration, end_var, "interval" + suffix) #Model the interval between start and end
                all_tasks[job_id, task_id] = task_type(start=start_var, end=end_var, interval=interval_var) #Add this task to dictionary of all tasks
                machine_to_intervals[machine].append(interval_var) #Add the interval to the list of tasks for this machine

            elif operation == "react":
                task_id = 2
                task = (task_df[1]["Reactor"] + 1, int(np.ceil(task_df[1]["Duration (Ds)"]))) #use the reactor
                task_list.append(task)

                machine, duration = task #Unpack the tuple
                suffix = f"_{job_id}_{task_id}" #Create suffics for the variables
                start_var = model.new_int_var(0, horizon, "start" + suffix) #Start of this task can be anywhere between 0 and horizon
                end_var = model.new_int_var(0, horizon, "end" + suffix) #End of this task can be anywhere between 0 and horizon
                interval_var = model.new_interval_var(start_var, duration, end_var, "interval" + suffix) #Model the interval between start and end
                all_tasks[job_id, task_id] = task_type(start=start_var, end=end_var, interval=interval_var) #Add this task to dictionary of all tasks
                machine_to_intervals[machine].append(interval_var) #Add the interval to the list of tasks for this machine

            elif operation == "move_to_centrifuge":
                task_id = 3
                task = (0, int(np.ceil(task_df[1]["Duration (Ds)"]))) #use the arm&clamp to move the sample to the centrifuge
                task_list.append(task)

                machine, duration = task #Unpack the tuple
                suffix = f"_{job_id}_{task_id}" #Create suffics for the variables
                start_var = model.new_int_var(0, horizon, "start" + suffix) #Start of this task can be anywhere between 0 and horizon
                end_var = model.new_int_var(0, horizon, "end" + suffix) #End of this task can be anywhere between 0 and horizon
                interval_var = model.new_interval_var(start_var, duration, end_var, "interval" + suffix) #Model the interval between start and end
                all_tasks[job_id, task_id] = task_type(start=start_var, end=end_var, interval=interval_var) #Add this task to dictionary of all tasks
                machine_to_intervals[machine].append(interval_var) #Add the interval to the list of tasks for this machine

            elif operation == "centrifuge":
                task_id = 4
                task = (reactors + 1, int(np.ceil(task_df[1]["Duration (Ds)"]))) #use the centrifuge
                task_list.append(task)

                machine, duration = task #Unpack the tuple
                suffix = f"_{job_id}_{task_id}" #Create suffics for the variables
                start_var = model.new_int_var(0, horizon, "start" + suffix) #Start of this task can be anywhere between 0 and horizon
                end_var = model.new_int_var(0, horizon, "end" + suffix) #End of this task can be anywhere between 0 and horizon
                interval_var = model.new_interval_var(start_var, duration, end_var, "interval" + suffix) #Model the interval between start and end
                all_tasks[job_id, task_id] = task_type(start=start_var, end=end_var, interval=interval_var) #Add this task to dictionary of all tasks
                machine_to_intervals[machine].append(interval_var) #Add the interval to the list of tasks for this machine
            
            elif operation == "rm_supernatent":
                task_id = 5
                task = (0, int(np.ceil(task_df[1]["Duration (Ds)"]))) #rm_supernatent only uses the arm&clamp
                task_list.append(task)

                machine, duration = task #Unpack the tuple
                suffix = f"_{job_id}_{task_id}" #Create suffics for the variables
                start_var = model.new_int_var(0, horizon, "start" + suffix) #Start of this task can be anywhere between 0 and horizon
                end_var = model.new_int_var(0, horizon, "end" + suffix) #End of this task can be anywhere between 0 and horizon
                interval_var = model.new_interval_var(start_var, duration, end_var, "interval" + suffix) #Model the interval between start and end
                all_tasks[job_id, task_id] = task_type(start=start_var, end=end_var, interval=interval_var) #Add this task to dictionary of all tasks
                machine_to_intervals[machine].append(interval_var) #Add the interval to the list of tasks for this machine
            
            elif operation == "move_to_sonicator":
                task_id = 6
                task = (0, int(np.ceil(task_df[1]["Duration (Ds)"]))) #use the arm&clamp to move the sample to the sonicator
                task_list.append(task)

                machine, duration = task #Unpack the tuple
                suffix = f"_{job_id}_{task_id}" #Create suffics for the variables
                start_var = model.new_int_var(0, horizon, "start" + suffix) #Start of this task can be anywhere between 0 and horizon
                end_var = model.new_int_var(0, horizon, "end" + suffix) #End of this task can be anywhere between 0 and horizon
                interval_var = model.new_interval_var(start_var, duration, end_var, "interval" + suffix) #Model the interval between start and end
                all_tasks[job_id, task_id] = task_type(start=start_var, end=end_var, interval=interval_var) #Add this task to dictionary of all tasks
                machine_to_intervals[machine].append(interval_var) #Add the interval to the list of tasks for this machine
            
            elif operation == "sonicate":
                task_id = 7
                
                task = (reactors + 2, int(np.ceil(task_df[1]["Sonicator Duration (Ds)"]))) #use the sonicator
                task_list.append(task)

                machine, duration = task #Unpack the tuple
                suffix = f"_{job_id}_{task_id}" #Create suffics for the variables
                start_var = model.new_int_var(0, horizon, "start" + suffix) #Start of this task can be anywhere between 0 and horizon
                end_var = model.new_int_var(0, horizon, "end" + suffix) #End of this task can be anywhere between 0 and horizon
                interval_var = model.new_interval_var(start_var, duration, end_var, "interval" + suffix) #Model the interval between start and end
                all_tasks[job_id, task_id] = task_type(start=start_var, end=end_var, interval=interval_var) #Add this task to dictionary of all tasks
                machine_to_intervals[machine].append(interval_var) #Add the interval to the list of tasks for this machine


        job_list.append(task_list)



    ##### Add constraints to the model ####

    # For the Arm&Clamp, sonicator, and centrifuge add no_overlap constraint
    model.add_no_overlap(machine_to_intervals[0]) #Arm&Clamp no_overlap constraint
    model.add_no_overlap(machine_to_intervals[reactors + 1]) #Centrifuge no_overlap constraint
    model.add_no_overlap(machine_to_intervals[reactors + 2]) #Sonicator no_overlap constraint


    # Precedences inside a job. (In each job, the next task must start after the previous task ends)
    for job_id, job in enumerate(job_list):
        for task_id in range(len(job) - 1):
            model.add(
                all_tasks[job_id, task_id + 1].start >= all_tasks[job_id, task_id].end
            )
    #Constrain the "move_to_reactor" operations end at the same time as the start of the "react" operation
    for job_id, sample_name in enumerate(sample_names):
            #Get all the unit ops for that sample
            sub_df = unit_ops_df[unit_ops_df["Sample Name"] == sample_name]

            for task_df in sub_df.iterrows():

              operation = task_df[1]["UnitOP"]

              if operation == "move_to_reactor":
                task_id = 1 #Move to reactor task is always task 1, and react is always task 2
                model.add(
                  all_tasks[job_id, task_id].end == all_tasks[job_id, task_id + 1].start
                )

              
    # Constrain the reactor jobs: overlapping reactions on the reactor need to END at the same time, 
    # and sequental reactions on the reactor should start with lower temperature reactions 
    for reactor in range(reactors):
      sub_df = unit_ops_df[unit_ops_df["Reactor"] == reactor]

      temperatures = np.unique(sub_df["Reactor Temperature (C)"].to_numpy())

      samples_using_this_reactor = sub_df["Sample Name"].to_numpy()
      sample_name_index = np.argwhere(np.isin(sample_names, samples_using_this_reactor)).flatten()
     
      print(f"Temperatures on each reactor = {temperatures}")
      print(samples_using_this_reactor)
      print(sample_name_index)
      print(machine_to_intervals[reactor+1])
      for job_a, sample_a in zip(sample_name_index, samples_using_this_reactor):
         for job_b, sample_b in zip(sample_name_index, samples_using_this_reactor):
            

      longest_sample_duration_at_each_temp = []

      # Add constraint for: with the same reactor and the same temperature, the end times should be the same
      for temp in temperatures:

        samples_at_that_temp = sub_df[sub_df["Reactor Temperature (C)"] == temp]["Sample Name"].to_numpy()
        sample_name_index = np.argwhere(np.isin(sample_names, samples_at_that_temp)).flatten()

        for i in sample_name_index:
          for j in sample_name_index:
            if i != j:
              if i < j:
                model.add(
                    all_tasks[i, 1].end == all_tasks[j, 1].end #Job i, task 1 (react) must end at the same time as Job j, task 1
                )
        #Get the piece of the dataframe that is at that temperature
        sub_sub_df = sub_df[sub_df["Reactor Temperature (C)"] == temp]
        #Sort that piece of dataframe by the reactor duration
        sub_sub_df = sub_sub_df.sort_values("Duration (Ds)")


        #Add the sample with the longest duration to the list
        longest_sample_duration_at_each_temp.append(sub_sub_df["Sample Name"].to_numpy()[-1])

      #Add constraint for: with the same reactor the lower temperature should start first
      if len(longest_sample_duration_at_each_temp) > 1:
        for i, name in enumerate(longest_sample_duration_at_each_temp[:-1]):
          low_temp_sample_index = np.argwhere(sample_names == name).flatten()[0]
          high_temp_sample_index = np.argwhere(sample_names == longest_sample_duration_at_each_temp[i+1]).flatten()[0]
          model.add(
              all_tasks[low_temp_sample_index, 1].end <= all_tasks[high_temp_sample_index, 1].start #Low temp react task must end before high temp react task can start
          )

    # Makespan objective.
    obj_var = model.new_int_var(0, horizon, "makespan")
    model.add_max_equality(
        obj_var,
        [all_tasks[job_id, len(job) - 1].end for job_id, job in enumerate(job_list)],
    )
    model.minimize(obj_var)


    ########### Solve #############
    solver = cp_model.CpSolver()
    status = solver.solve(model)


    ###### Display Solution ######
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("Solution:")
        # Create one list of assigned tasks per machine.
        assigned_jobs = collections.defaultdict(list)
        for job_id, job in enumerate(job_list):
            for task_id, task in enumerate(job):
                machine = task[0]
                assigned_jobs[machine].append(
                    assigned_task_type(
                        start=solver.value(all_tasks[job_id, task_id].start),
                        job=job_id,
                        index=task_id,
                        duration=task[1],
                    )
                )

        # Create per machine output lines.
        output = ""
        for machine in all_machines:
            # Sort by starting time.
            assigned_jobs[machine].sort()
            sol_line_tasks = "Machine " + str(machine) + ": "
            sol_line = "           "

            for assigned_task in assigned_jobs[machine]:
                name = f"job_{assigned_task.job}_task_{assigned_task.index}"
                # add spaces to output to align columns.
                sol_line_tasks += f"{name:15}"

                start = assigned_task.start
                duration = assigned_task.duration
                sol_tmp = f"[{start},{start + duration}]"
                # add spaces to output to align columns.
                sol_line += f"{sol_tmp:15}"

            sol_line += "\n"
            sol_line_tasks += "\n"
            output += sol_line_tasks
            output += sol_line

        # Finally print the solution found.
        print(f"Optimal Schedule Length: {solver.objective_value}")
        print(output)
    else:
        print("No solution found.")
