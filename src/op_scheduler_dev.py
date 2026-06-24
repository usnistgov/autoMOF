import pandas as pd

import numpy as np

import collections
from ortools.sat.python import cp_model

from .experiments import Ternary_colordemo, Cu_BTC
from .schedule_plotter import plot_gantt_chart

import copy

#TODO encode some logic for the case where there are more reactions at the same temperature than there are positions in the same reactor!!!
def reactor_use_assignment(reactor_df, number_of_reactors, positions_in_reactor):
  """
  This function reads the reactor dataframe
  and if there are more reactors needed than are available,
  merge the shortest durations to the same reactor (to happen sequentially). 
  
  Keep doing that until the reactor dataframe uses at most the same number as available reactors. 

  Parameters
  ----------
  reactor_df : pd.DataFrame
    DataFrame that keeps track of each experiment on each reactor
  number_of_reactors : int
    The number of reactors on the platform
  positions_in_reactor : int
    The number of positions in each reactor

  Returns
  -------
  reactor_df : pd.DataFrame
    DataFrame that keeps track of each experiment on each reactor
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
  """
  Read the unit operations dataframe and assign reactor IDs to each react operation

  Reactions at the same temperature should be on the same reactor (unless this is more than can fit).
  Reactors can be re-used for several groups of reactions 
  Shortest durations of groups of reactions get merged to the same reactor. 
  Until all of the react unit operations are assigned to one of the available reactors. 

  Parameters
  ----------
  unit_ops_df : pd.DataFrame
    DataFrame that keeps track of each step of each experiment
  number_of_reactors : int
    The number of reactors on the platform
  positions_in_reactor : int
    The number of positions in each reactor

  Returns
  -------
  unit_ops_df : pd.DataFrame
    DataFrame that keeps track of each step of each experiment
  reactor_df : pd.DataFrame
    DataFrame that keeps track of each experiment on each reactor
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
      if len(sub_df) > 0:
        temps = list(sub_df["Reactor Temperature (C)"])[0]

        #If the reaction temperature is in the list of temperatures for that reactor
        if temperature in temps:
            #Assign that reactor
            unit_ops_df.at[i, "Reactor"] = reactor


  return unit_ops_df, reactor_df


def define_machine_IDs(reactors, centrifuge = 1, sonicator = 1):
  """
  Function that creates objects to keep track of the components (aka machines) on the platform.
  Arm&Clamp is machine 0
  Then add each reactor, then add each centrifuge, then add each sonicator

  Parameters
  ----------
  reactors : int
    The number of reactors
  centrifuge : int
    The number of centrifuges
  sonicator : int
    The number of sonicators

  Returns
  -------
  machine_id : list
    List of strings of each name of each machine in order
  machine_count : int
    Number of machines on the platform
  all_machines : range
    Range of each index of each machine
  """
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
                       Wash_Cycles = 6,
                       Dry = True,
                       Centrifuge = False,
                       Remove_supernatent = False,
                       Sonicate = False):

    """
    Function for creating a DataFrame of the Unit Ops and sub_unit ops
    for each sample. Uses hard-coded durations for the Arm&Clamp movements

    Durations are in Ds - so that there is fine enough fidelity, but still an integer (as needed for constraint solver)
    
    Which unit ops are performed and added to the dataframe is controled by the boolean flags, or ints.
    
    Parameters
    ----------
    sample_db : dict
        Dictionary that lists the details of each sample
    Add_fluids : bool
        Flag for adding the UnitOP for adding precursors
    React : bool
        Flag for adding the UnitOP for reacting
    Wash_Cycles : int
        Number of wash cycles to include. 
        Each wash cycle adds UnitOPs for: 
            Centrifuge, 
            Removeing Supernatent,
            Adding Solvents
            Sonicate
            Rack Hold
    Dry : bool
        Flag for adding the UnitOP for drying reactants
    Centrifuge : bool
        Flag for adding an individual UnitOP for centrifuge
    Remove_supernatent : bool
        Flag for adding an individual UnitOP for removeing the supernatent
    Sonicate : bool
        Flag for adding an individual UnitOP for sonicating

    Returns
    -------
    unit_ops_df : pd.DataFrame
        DataFrame that keeps track of each step of each experiment
    op_order : list
        List of the names of each UnitOP in the order they should happen for each sample
    """


    header = ["Sample Name", "UnitOP", "Duration (Ds)", "Reactor", "Reactor Temperature (C)"]
    unit_ops_df = pd.DataFrame(columns = header)
    for key in sample_db.keys():
        
        if Add_fluids == True:
            sub_df = pd.DataFrame([[key, "add_fluids", 2*6, None, 0]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])

        if React == True:
            temp = sample_db[key]["Temperature (C)"] 
            time = sample_db[key]["Reaction Time (min)"] 

            sub_df = pd.DataFrame([[key, "react", time*6, None, temp]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])

        for i in range(Wash_Cycles):
            sub_df = pd.DataFrame([[key, f"centrifuge_{i}", 40*6, None, 0],
                                   [key, f"rm_supernatent_{i}", 2*6, None, 0],
                                   [key, f"add_solvents_{i}", 2*6, None, 0],
                                   [key, f"sonicate_{i}", 60*6, None, 0],
                                   [key, f"rack_hold_{i}", 24*60*6, None, 0]], 
                                   columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])

        if Dry == True:
            sub_df = pd.DataFrame([[key, f"centrifuge_{0+Wash_Cycles}", 40*6, None, 0],
                                   [key, f"rm_supernatent_{0+Wash_Cycles}", 2*6, None, 0],
                                   [key, "dry", 24*60*6, None, 100]], 
                                   columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])
           

        if Centrifuge == True:
            sub_df = pd.DataFrame([[key, "centrifuge", 40*6, None, 0]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])

        if Remove_supernatent == True:
            sub_df = pd.DataFrame([[key, "rm_supernatent", 2*6, None, 0]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])
        
        if Sonicate == True:
            sub_df = pd.DataFrame([[key, "sonicate", 60*6, None, 0]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])

    unit_ops_df["Status"] = "To Do"

    seen = dict()
    op_order = np.array([seen.setdefault(x, x) for x in unit_ops_df["UnitOP"].to_numpy() if x not in seen]).tolist()

    return unit_ops_df, op_order


def build_job_shop_var_containers(unit_ops_df, num_reactors, op_order):
    """
    Function to build the containers to keep track of the variables for the job shop problem.
    Note that the reactors for the react UnitOPs are assigned by the assign_reactors function,
    but the reactor assignments for any drying steps are as yet unknown, and will be variables.

    This function creates the initial containers, and populates them with any known quatities.
    Any job shop variables are assigned subsequently, overwiting the NaNs.

    Parameters
    ----------
    unit_ops_df : pd.DataFrame
        DataFrame that keeps track of each step of each experiment
    num_reactors : int
        The number of reactors on the platform
    op_order : list
        List of the names of each UnitOP in the order they should happen for each sample

    Returns
    -------
    resource_dict : dict
        Dictionary of what resource each UnitOP is using for each sample. 
        Resources are counted by machine_ID, O is Arm&Clamp then reactors, the centrifuges, then sonicators, the vial rack
    interval_dict : dict
        Dictionary of each interval variable for each UnitOP for each sample.
    """

    #Treating the dictionary as a 2D array, columns are UnitOPs, rows are samples.
    #Column headers
    columns = ["Sample Name"] + op_order
    #Row headers
    rows = unit_ops_df["Sample Name"].unique().tolist()

    #Create initial containers with NaNs for the empty variables
    interval_dict = {"Sample Name": rows}
    for op in op_order:
        interval_dict[op] = (np.empty(len(rows))*np.nan).tolist()
    #Make an independant copy
    resource_dict = copy.deepcopy(interval_dict)
    
    #Populate the resource dict with the reactor assignments for the react UnitOPs
    resource_dict["react"] =  (unit_ops_df[unit_ops_df["UnitOP"] == "react"]["Reactor"].to_numpy() + 1).tolist()

    for col in resource_dict.keys():
        if col == "add_fluids":
            resource_dict[col] = (np.zeros(len(rows), dtype=int)).tolist()
        if "centrifuge" in col:
            resource_dict[col] = (np.zeros(len(rows), dtype=int) + num_reactors + 1).tolist()
        if "rm_supernatent" in col:
            resource_dict[col] = (np.zeros(len(rows), dtype=int)).tolist() 
        if "add_solvents" in col:
            resource_dict[col] = (np.zeros(len(rows), dtype=int)).tolist() 
        if "sonicate" in col:
            resource_dict[col] = (np.zeros(len(rows), dtype=int) + num_reactors + 2).tolist()
        if "rack_hold" in col:
            resource_dict[col] = (np.zeros(len(rows), dtype=int) + num_reactors + 3).tolist()

    return resource_dict, interval_dict

def dict_indexer(dictionary, sample, op):
    """
    Function to index into dictionary by sample (aka row), and UnitOP (aka column)
    
    Parameters
    ----------
    dictionary : dict
        Dictionary to index into
    sample : str
        Name of the sample, indexes into the rows
    op : str
        Name of the UnitOP, indexes into the column
    
    Returns
    -------
    dictionary[op][dict_ind] : any
        Object at that column and row index
    """
    dict_ind = dictionary["Sample Name"].index(sample)
    return dictionary[op][dict_ind]

def dict_assigner(dictionary, sample, op, new_value):
    """
    Function to assign a new value to a particular sample (aka row), and UnitOP (aka column) index
    
    Parameters
    ----------
    dictionary : dict
        Dictionary to assign a new value to at an particular index
    sample : str
        Name of the sample, indexes into the rows
    op : str
        Name of the UnitOP, indexes into the column
    new_value : any
        Object to assign to that index in the dictionary
    
    Returns
    -------
    dictionary : dict
        Dictionary with new value assigned
    """
    dict_ind = dictionary["Sample Name"].index(sample)
    dictionary[op][dict_ind] = new_value
    return dictionary

def dict_row_slicer(dictionary, sample):
    """
    Function to find all the rows for a sample (aka row)

    Parameters
    ----------
    dictionary : dict
        Dictionary to index into
    sample : str
        Name of the sample, indexes into the rows

    Returns
    -------
    values : list
        List of objects in that row
    """
    values = []
    for col in dictionary.keys():
        if col != "Sample Name":
            value = dict_indexer(dictionary, sample, col)
            values.append(value)
    return values
    

def dict_searcher(dictionary, value):
    """
    Function to find all the (sample, op) pairs that use a particular resource (value in the dictionary), then report those intervals (indexes)
    
    Parameters
    ----------
    dictionary : dict
        Dictionary to index into
    value : int
        value to search the dictionary  for
    
    Returns
    -------
    discovered_inds : list
        List of tuples of indexes (sample, op) that have that value.
    """
    discovered_inds = []
    for key in dictionary.keys():
        try:
            dict_index = np.where(np.array(dictionary[key]) == value)[0]
            samples = [dictionary["Sample Name"][i] for i in dict_index]
            ops = [key] * len(samples)
            for sample, op in zip(samples, ops):
                discovered_inds.append((sample, op))
        except:
            pass
    return discovered_inds

def dict_reporter(dictionary, inds):
    """
    Funtion to report all the values of a dictionary at particular (sample, op) indexes

    Parameters
    ----------
    dictionary : dict
        Dictionary to index into
    inds : list
        List of tuples of (sample, op).
    
    Returns
    -------
    values : list
        List of objects that use that resource.
    """
    values = []
    for i in inds:
        value = dict_indexer(dictionary, i[0], i[1])
        values.append(value)

    return values

def dict_multi_assigner(dictionary, inds, new_value):
    """
    Function to assign a new value to several indexes (sample, op)

    Parameters
    ----------
    dictionary : dict
        Dictionary to index into
    inds : list
        List of tuples of (sample, op)
    new_value : any
        Object to assign to that index in the dictionary

    Returns
    -------
    dictionary : dict
        Dictionary with new values assigned
    """
    for i in inds:
        dictionary = dict_assigner(dictionary, i[0], i[1], new_value)
    return dictionary

def add_unit_ops_resource_collumn(unit_ops_df):
    """
    Fuction to assign the name of the resource to each UnitOP for each sample in the unit_ops_df.
    
    Parameters
    ----------
    Parameters
    ----------
    unit_ops_df : pd.DataFrame
        DataFrame that keeps track of each step of each experiment

    Returns
    -------
    unit_ops_df : pd.DataFrame
        DataFrame that keeps track of each step of each experiment
    """
    
    for idx, row in unit_ops_df.iterrows():
      if row["UnitOP"] == "add_fluids":
          unit_ops_df.loc[idx,"Resource"] = "Arm&Clamp"
      if row["UnitOP"] == "react":
          unit_ops_df.loc[idx,"Resource"] = f"Reactor {row["Reactor"]}"
      if row["UnitOP"] == "pre_heat_reactor":
          unit_ops_df.loc[idx,"Resource"] = f"Reactor {row["Reactor"]}"
      if "centrifuge" in row["UnitOP"]:
          unit_ops_df.loc[idx,"Resource"] = "Centrifuge"
      if "rm_supernatent" in row["UnitOP"]:
          unit_ops_df.loc[idx,"Resource"] = "Arm&Clamp"
      if "add_solvents" in row["UnitOP"]:
          unit_ops_df.loc[idx,"Resource"] = "Arm&Clamp"
      if "sonicate" in row["UnitOP"]:
          unit_ops_df.loc[idx,"Resource"] = "Sonicator"
      if "rack_hold" in row["UnitOP"]:
          unit_ops_df.loc[idx,"Resource"] = "VialRack"
      if row["UnitOP"] == "dry":
          unit_ops_df.loc[idx,"Resource"] = f"Reactor {row["Reactor"]}"

         
    return unit_ops_df

def solve_job_shop_schedule(unit_ops_df, num_reactors, op_order, plot = False):
    """
    Function to create, then solve the job shop schedule problem.


    Parameters
    ----------
    unit_ops_df : pd.DataFrame
        DataFrame that keeps track of each step of each experiment
    num_reactors : int
        The number of reactors on the platform
    op_order : list
        List of the names of each UnitOP in the order they should happen for each sample

    Returns
    -------
    unit_ops_df : pd.DataFrame
        DataFrame that keeps track of each step of each experiment
    """

    #Find the maximum possible time for all UnitOPs performed in sequence
    horizon = int(np.sum(np.ceil(unit_ops_df["Duration (Ds)"])))

    # Named tuple to store information about created variables.
    task_type = collections.namedtuple("task_type", "start end interval")
    # Named tuple to manipulate solution information.
    assigned_task_type = collections.namedtuple("assigned_task_type", "start job index duration")

    #Initialize the model
    model = cp_model.CpModel()

    #Create the inital cotainers to keep track of resources and intervals
    resource_dict, interval_dict = build_job_shop_var_containers(unit_ops_df, num_reactors, op_order)

    #Create some additional containers for the drying UnitOPs
    dry_interval_vars = []
    dry_machine_vars = []
    dry_bool_vars = []
    optional_intervals = []
    dryer_assignments = []


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Creating all the variables for the job shop problem
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    #Create new interval variables for all UnitOps EXCEPT the drying OPs
    for col in interval_dict.keys():
        for i, sample in enumerate(interval_dict["Sample Name"]):
            if col != "Sample Name":
                if not "dry" in col:
                    # duration = unit_ops_df[(unit_ops_df["Sample Name"] == sample) & 
                    #                     (unit_ops_df["UnitOP"] == col)]["Duration (Ds)"].values[0]
                    duration = unit_ops_df[(unit_ops_df["Sample Name"] == sample) & 
                                        (unit_ops_df["UnitOP"] == col)]["Duration (Ds)"].values
                    if len(duration) > 0:
                        duration = duration[0]
                        duration = int(np.ceil(duration))
                        suffix = f"_{sample}_{col}"
                        start_var = model.new_int_var(0, horizon, "start" + suffix) #Start of this task can be anywhere between 0 and horizon
                        end_var = model.new_int_var(0, horizon, "end" + suffix) #End of this task can be anywhere between 0 and horizon
                        interval_var = model.new_interval_var(start_var, duration, end_var, "interval" + suffix) #Model the interval between start and end
                        task = task_type(start=start_var, end=end_var, interval=interval_var) #Create a task
                        interval_dict = dict_assigner(interval_dict, sample, col, task)#Add this task to dictionary of all tasks


    #Create a new bool_var and optional_interval_var for every dry OP for every reactor
    for i in range(num_reactors):
        m = i + 1 #Convert to Machine ID
        optional_intervals_per_machine = []
        for i, sample in enumerate(interval_dict["Sample Name"]):
            suffix = f"_dry_{sample}_{m}"
            b = model.NewBoolVar("bool_" + suffix)
            dryer_assignments.append(b)
            duration = unit_ops_df[(unit_ops_df["Sample Name"] == sample) & 
                                        (unit_ops_df["UnitOP"] == "dry")]["Duration (Ds)"].values[0]
            duration = int(np.ceil(duration))
            start_var = model.new_int_var(0, horizon, "start" + suffix) #Start of this task can be anywhere between 0 and horizon
            end_var = model.new_int_var(0, horizon, "end" + suffix) #End of this task can be anywhere between 0 and horizon
            optional_interval = model.NewOptionalIntervalVar(start_var,
                                                            duration,
                                                            end_var, 
                                                            b, 
                                                            "Optional_interval"+suffix)
            optional_intervals_per_machine.append(optional_interval)
        optional_intervals.append(optional_intervals_per_machine)

    #Assign the list of optional interval vars fro the dry OPs to the interval dict
    for sample in interval_dict["Sample Name"]:
        dry_sample_intervals = []
        for interval in optional_intervals:
            for inv in interval:
                if sample in inv.name:
                    dry_sample_intervals.append(inv)

        interval_dict = dict_assigner(interval_dict, sample, "dry", dry_sample_intervals)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Applying all the constraints for the job shop problem
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    #Find all the tasks that use the Arm&Clamp, and impose no_overlap constraint
    dict_inds = dict_searcher(resource_dict, 0)
    arm_tasks = dict_reporter(interval_dict, dict_inds)
    arm_intervals = [task.interval for task in arm_tasks]
    model.add_no_overlap(arm_intervals)

    #For each sample all the ops must happen in order
    for i, sample in enumerate(interval_dict["Sample Name"]):
        #Find all the tasks for that sample
        sample_tasks = dict_row_slicer(interval_dict, sample)

        #Iterate through those tasks
        for i, sample_task in enumerate(sample_tasks):
            if i != 0: 
                #If the task is a interval task_type (most OPs are), then it must start after the previous task ends
                if type(sample_task) == task_type:
                    model.add(sample_tasks[i-1].end <= sample_task.start)
                #If the task is a list (the drying tasks are), then iteratate through that list and consrain each.
                # Note, assumes that the previous task is a interval task_type
                # Works if the drying task is the last task for each sample. 
                elif type(sample_task) == list:
                    for alt_task in sample_task:
                        model.add(sample_tasks[i-1].end <= alt_task.start_expr()) 

    #Constrain the Capacity of the Dry Ops
    #Constrain bool_vars so each sample can only choose one
    for sample in resource_dict["Sample Name"]:
        truth_list = [sample in b.name for b in dryer_assignments]
        indexs = np.where(np.array(truth_list) == True)[0]
        bools_for_sample = [dryer_assignments[i] for i in indexs]
        model.AddExactlyOne(bools_for_sample)

    #Constrain the capacity of the dryers
    #  each optional interval has a demand of 1
    #  each reactor has a capacity of 4
    for optional_intervals_per_machine in optional_intervals:
        model.AddCumulative(optional_intervals_per_machine, 
                            [1] * len(optional_intervals_per_machine), 
                            4 
                            )
    
    #No Overlap between drying and reacting on the same machine
    for i, optional_intervals_per_machine in enumerate(optional_intervals):
        m = i+1 #Convert index to Machine ID
        react_inds = dict_searcher(resource_dict, m)
        react_tasks = dict_reporter(interval_dict, react_inds)

        for task in react_tasks:
            for optional_interval in optional_intervals_per_machine:
                exclusive_intervals = [optional_interval, task.interval] 
                model.add_no_overlap(exclusive_intervals)

    #Find all the tasks that use each reactor, and impose capacity constraint
    for i in range(num_reactors):
        machine = i+1 #Convert index to Machine ID
        dict_inds = dict_searcher(resource_dict, machine)
        reactor_tasks = dict_reporter(interval_dict, dict_inds)
        reactor_intervals = [task.interval for task in reactor_tasks]
        demands = np.ones(len(reactor_tasks), dtype = int)

        model.AddCumulative(reactor_intervals, demands, 4)

    #Find all the tasks that use centrifuge, and impose capacity constraint
    dict_inds = dict_searcher(resource_dict, num_reactors + 1)
    centrifuge_tasks = dict_reporter(interval_dict, dict_inds)
    centrifuge_intervals = [task.interval for task in centrifuge_tasks]
    demands = np.ones(len(centrifuge_tasks), dtype = int)

    model.AddCumulative(centrifuge_intervals, demands, 6)

    #If centrifuge tasks overlap, then the start times should be equal, otherwise they should not overlap
    for i, cent_a in enumerate(centrifuge_tasks):
        for j, cent_b in enumerate(centrifuge_tasks):
            if i < j:
                
                b = model.NewBoolVar(f"centrifuge_overlap_{cent_a.interval.name}_{cent_b.interval.name}")
                b_order = model.NewBoolVar(f"centrifuge_order_{cent_a.interval.name}_{cent_b.interval.name}")
        
                model.Add(cent_a.start == cent_b.start).OnlyEnforceIf(b)
            
                model.Add(cent_a.end <= cent_b.start).OnlyEnforceIf(~b, b_order)
                model.Add(cent_b.end <= cent_a.start).OnlyEnforceIf(~b, ~b_order)

    #Find all the tasks that use sonicator, and impose capacity constraint
    dict_inds = dict_searcher(resource_dict, num_reactors + 2)
    sonicator_tasks = dict_reporter(interval_dict, dict_inds)
    sonicator_intervals = [task.interval for task in sonicator_tasks]
    demands = np.ones(len(sonicator_tasks), dtype = int)

    model.AddCumulative(sonicator_intervals, demands, 3) # Sonicator capacity


    # Add_fluids.end should be within 42 Ds of react.start for each sample
    for i, sample in enumerate(interval_dict["Sample Name"]):
        add_fluids_task = dict_indexer(interval_dict, sample, "add_fluids")
        react_task = dict_indexer(interval_dict, sample, "react")

        model.add(add_fluids_task.end + 42 > react_task.start)

    #Find all the reactions that happen at the same temperature and use the same reactor.
    # These must all END at the same time
    #Find all the reactions that use the same reactor but at different temperatures
    # the lower temperature should start first
    for reactor in range(num_reactors):
        sub_df = unit_ops_df[unit_ops_df["Reactor"] == reactor]
        temperatures = np.unique(sub_df["Reactor Temperature (C)"].to_numpy())
        longest_sample_duration_at_each_temp = []
        for temp in temperatures:
            samples_at_that_temp = sub_df[sub_df["Reactor Temperature (C)"] == temp]["Sample Name"].to_numpy()
            for i, sample_i in enumerate(samples_at_that_temp):
                for j, sample_j in enumerate(samples_at_that_temp):
                    if i < j:
                        react_task_i = dict_indexer(interval_dict, sample_i, "react")
                        react_task_j = dict_indexer(interval_dict, sample_j, "react")

                        model.add(react_task_i.end == react_task_j.end)
        
            #Get the piece of the dataframe that is at that temperature
            sub_sub_df = sub_df[sub_df["Reactor Temperature (C)"] == temp]
            #Sort that piece of dataframe by the reactor duration
            sub_sub_df = sub_sub_df.sort_values("Duration (Ds)")
            #Add the sample with the longest duration to the list
            longest_sample_duration_at_each_temp.append(sub_sub_df["Sample Name"].to_numpy()[-1])

        if len(longest_sample_duration_at_each_temp) > 1:
            for i, sample_i in enumerate(longest_sample_duration_at_each_temp[:-1]):
                sample_j = longest_sample_duration_at_each_temp[i+1]

                #Find low temperature react task
                react_task_i = dict_indexer(interval_dict, sample_i, "react")
                #Find high temperature react task
                react_task_j = dict_indexer(interval_dict, sample_j, "react")

                #Low temperature react task must end before the high temperature react task can start
                model.add(react_task_i.end <= react_task_j.start)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Creating objective for the job shop problem
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Makespan objective.
    obj_var = model.new_int_var(0, horizon, "makespan")

    #Gather the collections of tasks for every sample
    all_tasks = []
    for sample in interval_dict["Sample Name"]:
        all_tasks.extend(dict_row_slicer(interval_dict, sample))

    #Unpack all the tasks into a flat list of tasks
    all_tasks_list = []
    for task in all_tasks:
        if type(task) != list:
            all_tasks_list.append(task)
        else:
            for alt_task in task:
                all_tasks_list.append(alt_task)
    all_tasks_list = [item for item in all_tasks_list if type(item) != float]
    
    all_end_list = []
    for task in all_tasks_list:
        if type(task) == task_type:
            all_end_list.append(task.end)

    #Add the max_equality constraint
    model.add_max_equality(
        obj_var,
        all_end_list,
    )
    model.minimize(obj_var)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Solve the job shop problem
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    solver = cp_model.CpSolver()
    solver.parameters.randomize_search = True

    # solver.parameters.log_search_progress = True
    solver.parameters.log_search_progress = False

    # Custom log function, for example, using the Python logging module instead of stdout
    # Useful in a Jupyter notebook, where logging to stdout might not be visible
    solver.log_callback = print  # (str)->None
    # If using a custom log function, you can disable logging to stdout
    solver.parameters.log_to_stdout = False
    status = solver.solve(model)

    print("solver status", solver.status_name(status))

    # ~~~~~~~~~~~~~~~~~~~
    # Record the solution
    # ~~~~~~~~~~~~~~~~~~~

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:

        all_start_list = []

        for task in all_tasks_list:
            if type(task) == task_type:
                all_start_list.append(task.start)

        start_times = solver.values(all_start_list)

        end_times = solver.values(all_end_list)

        dry_machine_assignments = solver.values(dryer_assignments)
        dry_machine_assignments = dry_machine_assignments.to_list()

        #Find the machine index for the reactors assigned for each drying step
        ## Note that this is the global machine index, not the reactor index!
        assigned_reactors = []
        for sample in resource_dict["Sample Name"]:
            truth_list = [sample in b.name for b in dryer_assignments]
            indexs = np.where(np.array(truth_list) == True)[0]
            bools_for_sample = [dry_machine_assignments[i] for i in indexs]
            assigned_reactor = np.where(np.array(bools_for_sample) == 1)[0] + 1
            assigned_reactors.append(assigned_reactor[0])

        assigned_reactors = np.array(assigned_reactors)

        solved_dry_intervals = []
        for i, (r, sample) in enumerate(zip(assigned_reactors, resource_dict["Sample Name"])):
            solved_dry_intervals.append(optional_intervals[r-1][i]) #Subtract 1 to convert from Machine ID to reactor index
        
        drying_start_times = solver.values([interval.start_expr() for interval in solved_dry_intervals])
        drying_end_times = solver.values([interval.end_expr() for interval in solved_dry_intervals])

        unit_ops_df["Start Time (Ds)"] = "?"
        unit_ops_df["End Time (Ds)"] = "?"

        #Add the start times and end times to the unit ops df
        # Except for drying tasks
        for sample in interval_dict["Sample Name"]:
            truth_list = [sample in name.name for name in start_times.index.values]
            times_indexes = np.argwhere(truth_list)
            
            for op in op_order:
                if op != "dry":
                    op_truth_list = [op in name.name for name in start_times.index.values]
            
                    truth_test = np.array(op_truth_list) & np.array(truth_list)
                    time_index = np.argwhere(truth_test)
                    if len(time_index) > 0:
                        time_index = time_index[0][0]
                        unit_op_table_index = unit_ops_df[(unit_ops_df["Sample Name"] == sample) &
                                                        (unit_ops_df["UnitOP"] == op)].index.values[0]
                        unit_ops_df.loc[unit_op_table_index, "Start Time (Ds)"] = start_times.values[time_index]
                        unit_ops_df.loc[unit_op_table_index, "End Time (Ds)"] = end_times.values[time_index] 

        #Add the drying tasks start times and end times to the unit_ops_df
        for i, sample in enumerate(interval_dict["Sample Name"]):
            truth_list = [sample in name.name for name in drying_start_times.index.values]
            times_indexes = np.argwhere(truth_list)
            
            op = "dry"
            op_truth_list = [op in name.name for name in drying_start_times.index.values]

            truth_test = np.array(op_truth_list) & np.array(truth_list)
            time_index = np.argwhere(truth_test)
            if len(time_index) > 0:
                time_index = time_index[0][0]
                unit_op_table_index = unit_ops_df[(unit_ops_df["Sample Name"] == sample) &
                                                (unit_ops_df["UnitOP"] == op)].index.values[0]
                unit_ops_df.loc[unit_op_table_index, "Start Time (Ds)"] = drying_start_times.values[time_index]
                unit_ops_df.loc[unit_op_table_index, "End Time (Ds)"] = drying_end_times.values[time_index]     
                unit_ops_df.loc[unit_op_table_index, "Reactor"] = assigned_reactors[i] -1 # Subtract 1 to convert between Machine ID to reactor reactor index  

        unit_ops_df = add_unit_ops_resource_collumn(unit_ops_df)


        unit_ops_df["Step"] = unit_ops_df.index.values

        if plot == True:

            fig1, fig2, fig3 = plot_gantt_chart(unit_ops_df)

        unit_ops_df = unit_ops_df.sort_values("Start Time (Ds)")
        unit_ops_df.reset_index(inplace = True)

        if plot == True:
            return unit_ops_df, fig1, fig2, fig3
        
        else:
            return unit_ops_df
        
    else:
        raise(f"Status of solver is {status}")

def interleave_reactor_preheating(unit_ops_df, heating_rate):
  """
  Function for interleaving the pre_heat steps for the reactors.
  For a heating rate in C/min

  The logic is that it iterates though all the reaction OPs, 
    if the needed temperature is different than the previous temperature,
    insert a pre_heat step 
    Then ajust the pre_heat start times
        at the first reaction step, the pre_heat end just before the react starts
        at subsequent reaction steps, the pre_heat can start after the previous reaction ends
    Then all the affected reaction start times need to be adjusted.
        each react op that uses that reactor must start after the pre_heat completes
    Then if any samples had their react ops adjusted, 
        the same adjustment should apply to all subsequent ops for that sample
    Then every op should be adjusted so the first op starts at time = 0

  Parameters
  ----------
  unit_ops_df : pd.DataFrame
      DataFrame that keeps track of each step of each experiment
  heating_rate : float
      The heating rate that the reactor can achive, used for estimating time required to pre_heat

  Returns
  -------
  unit_ops_df : pd.DataFrame
      DataFrame that keeps track of each step of each experiment  
  """
  
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


