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
  # #Rename the old index colum to be the order of operations for each sample
  # unit_ops_df = unit_ops_df.rename(columns = {"index": "Op Order"})

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
            temp = sample_db[key]["Temperature (C)"] 
            time = sample_db[key]["Reaction Time (min)"] 

            sub_df = pd.DataFrame([[key, "react", time*6, None, temp]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])

        if Centrifuge == True:
            sub_df = pd.DataFrame([[key, "centrifuge", 10*6, None, 0]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])

        if Remove_supernatent == True:
            sub_df = pd.DataFrame([[key, "rm_supernatent", 3*6, None, 0]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])
        
        if Sonicate == True:
            sub_df = pd.DataFrame([[key, "sonicate", 5*6, None, 0]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])

    unit_ops_df["Status"] = "To Do"



    return unit_ops_df

def define_cp_job(unit_ops_df,
                  reactors, 
                  centrifuge = 1, 
                  sonicator = 1,
                  print_solution = False):

    """Function that reads the unit_ops_df,
    and creates a constraint satisfaction problem.
    Specifically a job shop problem. 
    The components of the robot are modeled as different "machines"

    Contraints:
    For each sample the operations must happen in order (add_fluids is before react, etc.)
    The arm&clamp can only handle 1 sample at a time
    Reactions that overlap on the same reactor must END at the same time. 

    """
    # #Get just the portion of the unit ops df that hasn't been scheduled yet. 
    # unit_ops_df = full_unit_ops_df[full_unit_ops_df["Status"] == "To Do"]
    # unit_ops_df = unit_ops_df.copy()
 
    #Order of operations
    op_order = ["add_fluids", "react", "centrifuge", "rm_supernatent", "sonicate"]
    unit_ops_df["Op Order"] = None
    op_order_df_index = unit_ops_df.columns.get_loc("Op Order")
    for i, row in unit_ops_df.iterrows():
        op_name = row["UnitOP"]
        op_pos = op_order.index(op_name)
        unit_ops_df.iloc[i, op_order_df_index] = op_pos

        

    #Start a container for all the jobs (a job is the collectons of each task for a sample)
    job_list = []

    #Initialize the model
    model = cp_model.CpModel()

    #Enumerate and name all the "machines"
    machine_id, machines_count, all_machines = define_machine_IDs(reactors, centrifuge, sonicator)

    #Calculate the total time horizon
    horizon = int(np.ceil(np.sum(unit_ops_df["Duration (Ds)"].to_numpy())))
    # print(f"Horizon = {horizon}")

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
                task_id = op_order.index("add_fluids")
                # task tuple: (machine id, duration)
                task = (0, int(np.ceil(task_df[1]["Duration (Ds)"]))) #Add_fluids only uses the arm&clamp
                task_list.append(task)

                machine, duration = task #Unpack the tuple
                suffix = f"_{job_id}_{task_id}" #Create suffics for the variables
                start_var = model.new_int_var(0, horizon, "start" + suffix) #Start of this task can be anywhere between 0 and horizon
                end_var = model.new_int_var(0, horizon, "end" + suffix) #End of this task can be anywhere between 0 and horizon
                interval_var = model.new_interval_var(start_var, duration, end_var, "interval" + suffix) #Model the interval between start and end
                all_tasks[job_id, task_id] = task_type(start=start_var, end=end_var, interval=interval_var) #Add this task to dictionary of all tasks
                machine_to_intervals[machine].append(interval_var) #Add the interval to the list of tasks for this machine

            elif operation == "react":
                task_id = op_order.index("react")
                # task tuple: (machine id, duration)
                task = (task_df[1]["Reactor"] + 1, int(np.ceil(task_df[1]["Duration (Ds)"]))) #use the reactor
                task_list.append(task)

                machine, duration = task #Unpack the tuple
                suffix = f"_{job_id}_{task_id}" #Create suffics for the variables
                start_var = model.new_int_var(0, horizon, "start" + suffix) #Start of this task can be anywhere between 0 and horizon
                end_var = model.new_int_var(0, horizon, "end" + suffix) #End of this task can be anywhere between 0 and horizon
                interval_var = model.new_interval_var(start_var, duration, end_var, "interval" + suffix) #Model the interval between start and end
                all_tasks[job_id, task_id] = task_type(start=start_var, end=end_var, interval=interval_var) #Add this task to dictionary of all tasks
                machine_to_intervals[machine].append(interval_var) #Add the interval to the list of tasks for this machine

            elif operation == "centrifuge":
                task_id = op_order.index("centrifuge")
                # task tuple: (machine id, duration)
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
                task_id = op_order.index("rm_supernatent")
                # task tuple: (machine id, duration)
                task = (0, int(np.ceil(task_df[1]["Duration (Ds)"]))) #rm_supernatent only uses the arm&clamp
                task_list.append(task)

                machine, duration = task #Unpack the tuple
                suffix = f"_{job_id}_{task_id}" #Create suffics for the variables
                start_var = model.new_int_var(0, horizon, "start" + suffix) #Start of this task can be anywhere between 0 and horizon
                end_var = model.new_int_var(0, horizon, "end" + suffix) #End of this task can be anywhere between 0 and horizon
                interval_var = model.new_interval_var(start_var, duration, end_var, "interval" + suffix) #Model the interval between start and end
                all_tasks[job_id, task_id] = task_type(start=start_var, end=end_var, interval=interval_var) #Add this task to dictionary of all tasks
                machine_to_intervals[machine].append(interval_var) #Add the interval to the list of tasks for this machine
            
            elif operation == "sonicate":
                task_id = op_order.index("sonicate")

                # task tuple: (machine id, duration)
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
    # Create a 2D array of [jobs, tasks]
    job_and_task = np.array(list(all_tasks.keys()))
    for j_and_t in job_and_task: #Iterate through the rows
       #check to see if there's another task for this job after this current task
       next_task = np.array([j_and_t[0], j_and_t[1]+1])
       if any((next_task == job_and_task).all(axis = 1)): # If the next task is in the list of jobs and tasks
          #Add the constraint that the next task must start after the current task ends
          model.add(
             all_tasks[next_task[0], next_task[1]].start >= all_tasks[j_and_t[0], j_and_t[1]].end
          )

    
    #Constrain the "add_fluids" to be within 42 Ds of the start of the "react"
    for job_id, sample_name in enumerate(sample_names):
            #Get all the unit ops for that sample
            sub_df = unit_ops_df[unit_ops_df["Sample Name"] == sample_name]
            for task_df in sub_df.iterrows():
              operation = task_df[1]["UnitOP"]

              if operation == "add_fluids":
                task_id = op_order.index("add_fluids")
                react_task_id = op_order.index("react")
                model.add(
                  all_tasks[job_id, task_id].start + 42 > all_tasks[job_id, react_task_id].start
                )

              
    # Constrain the reactor jobs: overlapping reactions on the reactor need to END at the same time, 
    # and sequental reactions on the reactor should start with lower temperature reactions 
    for reactor in range(reactors):
      sub_df = unit_ops_df[unit_ops_df["Reactor"] == reactor]

      temperatures = np.unique(sub_df["Reactor Temperature (C)"].to_numpy())

      # samples_using_this_reactor = sub_df["Sample Name"].to_numpy()
      # sample_name_index = np.argwhere(np.isin(sample_names, samples_using_this_reactor)).flatten()
     
      # # print(f"Temperatures on each reactor = {temperatures}")
      # # print(samples_using_this_reactor)
      # # print(sample_name_index)
      # # print(machine_to_intervals[reactor+1])
      # # for job_a, sample_a in zip(sample_name_index, samples_using_this_reactor):
      # #    for job_b, sample_b in zip(sample_name_index, samples_using_this_reactor):
            

      longest_sample_duration_at_each_temp = []

      # Add constraint for: with the same reactor and the same temperature, the end times should be the same
      for temp in temperatures:

        samples_at_that_temp = sub_df[sub_df["Reactor Temperature (C)"] == temp]["Sample Name"].to_numpy()
        sample_name_index = np.argwhere(np.isin(sample_names, samples_at_that_temp)).flatten()

        react_task_id = op_order.index("react")

        
        for i in sample_name_index:
          for j in sample_name_index:
            if i != j:
              if i < j:
                model.add(
                    all_tasks[i, react_task_id].end == all_tasks[j, react_task_id].end #Job i, task (react) must end at the same time as Job j, task (react)
                )


        #Get the piece of the dataframe that is at that temperature
        sub_sub_df = sub_df[sub_df["Reactor Temperature (C)"] == temp]
        #Sort that piece of dataframe by the reactor duration
        sub_sub_df = sub_sub_df.sort_values("Duration (Ds)")


        #Add the sample with the longest duration to the list
        longest_sample_duration_at_each_temp.append(sub_sub_df["Sample Name"].to_numpy()[-1])
      
      #Add constraint for: with the same reactor the lower temperature should start first
      react_op_idx = op_order.index("react")
      if len(longest_sample_duration_at_each_temp) > 1:
        for i, name in enumerate(longest_sample_duration_at_each_temp[:-1]):
          low_temp_sample_index = np.argwhere(sample_names == name).flatten()[0]
          high_temp_sample_index = np.argwhere(sample_names == longest_sample_duration_at_each_temp[i+1]).flatten()[0]
          
          #Low temp react task must end before high temp react task can start
          model.add(
              all_tasks[low_temp_sample_index, react_op_idx].end <= all_tasks[high_temp_sample_index, react_op_idx].start 
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


    ###### Record Solution ######
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:

        for key in all_tasks.keys():
           job_id = key[0]
           task_id = key[1]

           sample_name = sample_names[job_id]
           op_name = op_order[task_id]

           sub_df = unit_ops_df[unit_ops_df["Sample Name"] == sample_name]
           sub_sub_df = sub_df[sub_df["UnitOP"] == op_name]

           mask1 = unit_ops_df["Sample Name"] == sample_name
           mask2 = sub_df["UnitOP"] == op_name
           mask = mask1 & mask2
           row = unit_ops_df[mask].index

           start_time = solver.value(all_tasks[key].start)
           end_time = solver.value(all_tasks[key].end)

           unit_ops_df.loc[row, "Start Time (Ds)"] = start_time
           unit_ops_df.loc[row, "End Time (Ds)"] = end_time

        if print_solution == True:

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

    # unit_ops_df["Status"] = "To Do"

    #Sort by increasing start time and secondarily larger op orders (for ops that start at the same time, prefer to keep working on the sample further along)
    unit_ops_df = unit_ops_df.sort_values(["Start Time (Ds)", "Op Order"], ascending = [True, False])
    unit_ops_df = unit_ops_df.reset_index(drop = True)

    return unit_ops_df, solver.objective_value


def reset_schedule(full_unit_ops_df,
                  reactors, 
                  centrifuge = 1, 
                  sonicator = 1,
                  print_solution = False):
    
    #Find just the unit ops that have the status "To Do"
    unit_ops_df = full_unit_ops_df[full_unit_ops_df["Status"] == "To Do"]
    unit_ops_df = unit_ops_df.copy()
    unit_ops_df = unit_ops_df.reset_index(drop = True)


    #Re calculate the schedule (also resets the start time to 0)
    unit_ops_df, overall_time = define_cp_job(unit_ops_df, reactors, centrifuge, sonicator, print_solution)

    #Merge the new schedule into the original unit ops df
    condition = full_unit_ops_df["Status"] == "To Do"
    sub_df = full_unit_ops_df.loc[condition, :]
    for row in sub_df.iterrows():
        mask1 = unit_ops_df["Sample Name"] == row[1]["Sample Name"]
        mask2 = unit_ops_df["UnitOP"] == row[1]["UnitOP"]
        mask = mask1 & mask2

        #Overwrite with the new start and end times
        full_unit_ops_df.loc[row[0],"Start Time (Ds)"] = unit_ops_df.loc[mask,"Start Time (Ds)"].values
        full_unit_ops_df.loc[row[0],"End Time (Ds)"] = unit_ops_df.loc[mask,"End Time (Ds)"].values

    #Sort by increasing start time and secondarily larger op orders (for ops that start at the same time, prefer to keep working on the sample further along)
    full_unit_ops_df = full_unit_ops_df.sort_values(["Status", "Start Time (Ds)", "Op Order"], ascending = [True, True, False])

    return full_unit_ops_df
    
   


def interleave_reactor_preheating(unit_ops_df, heating_rate):
  """For a heating rate in C/mim"""
  
  heating_rate_DS = heating_rate * 10 /60 #Convert to C/Ds

  # Sort the DataFrame by 'Reactor', 'Start Time (Ds)'
  df_react = unit_ops_df[unit_ops_df['Reactor'].notnull()]
  df_react = df_react.sort_values(by=['Reactor', 'Start Time (Ds)'])

  # Initialize an empty list to store new rows
  new_rows = []

  # Iterate over each unique 'Reactor'
  for reactor in df_react['Reactor'].unique():
      reactor_df = df_react[df_react['Reactor'] == reactor]
      
      # Initialize previous temperature
      # prev_temp = None
      prev_temp = 20 # 20 C is room temp
      
      # Iterate over each row in the reactor DataFrame
      for i, (idx, row) in enumerate(reactor_df.iterrows()):
          if row['UnitOP'] == 'react':
              # Check if the temperature has changed
              if row['Reactor Temperature (C)'] != prev_temp:# and prev_temp is not None:
                  # Create a new row for 'pre_heat_reactor'
                  new_row = row.copy()
                  new_row['UnitOP'] = 'pre_heat_reactor'
                  current_temp = row['Reactor Temperature (C)']
                  duration = (current_temp - prev_temp)/heating_rate_DS # Time to get to temperature in Ds
                  
                  new_row['Duration (Ds)'] = duration
                  if i == 0:
                      new_row['Start Time (Ds)'] = row['Start Time (Ds)'] - duration  # Adjust start time
                      new_row['End Time (Ds)'] = new_row['Start Time (Ds)'] + duration  # End time is the same as start time
                  else:
                      prev_end_time = reactor_df.iloc[i -1]['End Time (Ds)']
                      new_row['Start Time (Ds)'] = prev_end_time 
                      new_row['End Time (Ds)'] = prev_end_time + duration
                  new_row['Op Order'] = 0 
                  new_row['Sample Name'] = None
                  
                  # Append the new row to the list
                  new_rows.append(new_row)
                  
              # Update previous temperature
              prev_temp = row['Reactor Temperature (C)']

  # Convert the list of new rows to a DataFrame
  new_rows_df = pd.DataFrame(new_rows)

  # Concatenate the original DataFrame with the new rows DataFrame
  unit_ops_df = pd.concat([unit_ops_df, new_rows_df]).sort_values(by=['Start Time (Ds)', 'Op Order']).reset_index(drop=True)

  # Identify 'pre_heat_reactor' and 'react' steps with the same reactor and temperature
  pre_heat_rows = unit_ops_df[unit_ops_df['UnitOP'] == 'pre_heat_reactor']
  react_rows = unit_ops_df[unit_ops_df['UnitOP'] == 'react']

  # Initialize a dictionary to store the shift amounts for each 'react' step
  shift_amounts = {}

  # Iterate through all the pre_heat unit ops
  for idx, pre_heat_row in pre_heat_rows.iterrows():
      # Find the corresponding 'react' step
      react_row = react_rows[(react_rows['Reactor'] == pre_heat_row['Reactor']) & 
                            (react_rows['Reactor Temperature (C)'] == pre_heat_row['Reactor Temperature (C)'])]
      
      if not react_row.empty:
          react_row = react_row.iloc[0]
          shift_amount = pre_heat_row['End Time (Ds)'] - react_row['Start Time (Ds)']

          if shift_amount > 0:
              # Store the shift amount
              shift_amounts[react_row.name] = shift_amount

  # Adjust the start and end times of the 'react' steps and subsequent steps
  for react_idx, shift_amount in shift_amounts.items():
      # Adjust subsequent 'react' steps with the same end time
      subsequent_react_rows = unit_ops_df[(unit_ops_df['UnitOP'] == 'react') & 
                                (unit_ops_df['Reactor'] == unit_ops_df.loc[react_idx, 'Reactor']) & 
                                (unit_ops_df['End Time (Ds)'] == unit_ops_df.loc[react_idx, 'End Time (Ds)'])]
      
      # Adjust the 'react' step
      unit_ops_df.loc[react_idx, 'Start Time (Ds)'] += shift_amount
      unit_ops_df.loc[react_idx, 'End Time (Ds)'] += shift_amount

      # Adjust subsequent steps for the same sample
      sample_name = unit_ops_df.loc[react_idx, 'Sample Name']
      subsequent_rows = unit_ops_df[(unit_ops_df['Sample Name'] == sample_name) & (unit_ops_df.index > react_idx)]
      unit_ops_df.loc[subsequent_rows.index, 'Start Time (Ds)'] += shift_amount
      unit_ops_df.loc[subsequent_rows.index, 'End Time (Ds)'] += shift_amount

      
      # Iterate through all the subsequent react steps that were adjusted
      for subsequent_react_idx in subsequent_react_rows.index:
          if subsequent_react_idx != react_idx:
              #Find the sample name for that reaction
              subsequent_sample_name = subsequent_react_rows.loc[subsequent_react_idx, 'Sample Name']
              #Adjust those reaction start and end times
              unit_ops_df.loc[subsequent_react_idx, 'Start Time (Ds)'] += shift_amount
              unit_ops_df.loc[subsequent_react_idx, 'End Time (Ds)'] += shift_amount

              #Find the other ops with that sample name at a higher index than the original reaction 
              other_subsequent_rows = unit_ops_df[(unit_ops_df['Sample Name'] == subsequent_sample_name) & 
                                                          (unit_ops_df['UnitOP'] != 'react') &
                                                          (unit_ops_df.index > react_idx)]
              #Adjust all those ops start and end times
              unit_ops_df.loc[other_subsequent_rows.index, 'Start Time (Ds)'] += shift_amount
              unit_ops_df.loc[other_subsequent_rows.index, 'End Time (Ds)'] += shift_amount
  
  #Shift all the ops so that the first op starts at time 0
  min_start = unit_ops_df["Start Time (Ds)"].min()

  if min_start < 0:
      shift = np.abs(min_start)

      unit_ops_df["Start Time (Ds)"] += shift
      unit_ops_df["End Time (Ds)"] += shift

  return unit_ops_df
      
def add_unit_ops_resource_collumn(unit_ops_df):
    for idx, row in unit_ops_df.iterrows():
      if row["UnitOP"] == "add_fluids":
          unit_ops_df.loc[idx,"Resource"] = "Arm&Clamp"
      if row["UnitOP"] == "react":
          unit_ops_df.loc[idx,"Resource"] = f"Reactor {row["Reactor"]}"
      if row["UnitOP"] == "pre_heat_reactor":
          unit_ops_df.loc[idx,"Resource"] = f"Reactor {row["Reactor"]}"
      if row["UnitOP"] == "sonicate":
          unit_ops_df.loc[idx,"Resource"] = "Sonicator"
      if row["UnitOP"] == "centrifuge":
          unit_ops_df.loc[idx,"Resource"] = "Centrifuge"
      if row["UnitOP"] == "rm_supernatent":
          unit_ops_df.loc[idx,"Resource"] = "Arm&Clamp"
    return unit_ops_df