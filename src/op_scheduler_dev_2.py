import pandas as pd

import numpy as np

import collections
import itertools
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

def add_unit_ops_resource_collumn(unit_ops_df):
    """
    Fuction to assign the name of the resource to each UnitOP for each sample in the unit_ops_df.
    
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


class Task:
    """
    Class representing a task in the job shop scheduling problem.

    Attributes
    ----------
    task_id : int 
        Unique identifier for the task.
    name : str
         Name of the task.
    duration : float
        Duration of the task in Ds.
    reactor : int
        Reactor ID assigned to the task.
    reactor_temp : float
        Temperature of the reactor for the task.
    resource : int or list
        Resource ID(s) assigned to the task.
    start_var : cp_model.IntVar or list
        Start time variable(s) for the task.
    end_var : cp_model.IntVar or list
        End time variable(s) for the task.
    interval_var : cp_model.IntervalVar or list
        Interval variable(s) for the task.

    Methods
    -------
    assign_resource(num_reactors)
        Assigns the machine ID for each resource based on the type of task.
    create_interval_var(model, horizon)
        Creates all the start, end, and interval variables for the constraint satisfaction model.
    """
    def __init__(self, task_id, name, duration, reactor, reactor_temp):
        self.task_id = task_id
        self.name = name
        self.duration = duration
        self.reactor = reactor
        self.reactor_temp = reactor_temp
        self.resource = None
        self.start_var = None
        self.end_var = None
        self.interval_var = None

    def assign_resouce(self, num_reactors):
        if "add_fluids" in self.name:
            self.resource = 0
        elif "react" in self.name:
            self.resource = 1 + self.reactor
        elif "centrifuge" in self.name:
            self.resource = num_reactors + 1
        elif "rm_supernatent" in self.name:
            self.resource = 0
        elif "add_solvents" in self.name:
            self.resource = 0
        elif "sonicate" in self.name:
            self.resource = num_reactors + 2
        elif "rack_hold" in self.name:
            self.resource = num_reactors + 3
        elif "dry" in self.name:
            self.resource = np.arange(num_reactors) + 1

    def create_interval_var(self, model, horizon):
        if "dry" not in self.name:
            duration_int = int(np.ceil(self.duration))
            self.start_var = model.new_int_var(0, horizon, f"start_{self.task_id}")
            self.end_var = model.new_int_var(0, horizon, f"end_{self.task_id}")
            self.interval_var = model.new_interval_var(self.start_var, duration_int, self.end_var, f"interval_{self.task_id}")
        elif "dry" in self.name:
            duration_int = int(np.ceil(self.duration))
            bool_vars = []
            start_vars = []
            end_vars = []
            interval_vars = []
            for resource in self.resource:
                bool_var = model.NewBoolVar(f"bool_{self.task_id}_{resource}") #Bool flag to choose this resouce

                start_var = model.new_int_var(0, horizon, f"start_{self.task_id}_{resource}")
                end_var = model.new_int_var(0, horizon, f"end_{self.task_id}_{resource}")

                optional_interval = model.NewOptionalIntervalVar(start_var,
                                                                 duration_int,
                                                                 end_var,
                                                                 bool_var,
                                                                 f"optional_interval_{self.task_id}_{resource}")
                
                bool_vars.append(bool_var)
                start_vars.append(start_var)
                end_vars.append(end_var)
                interval_vars.append(optional_interval)
            self.bool_vars = bool_vars
            self.start_var = start_vars
            self.end_var = end_vars
            self.interval_var = interval_vars

class Job:
    """
    Class representing a job (series of tasks) in the job shop scheduling problem.

    Attributes
    ----------
    job_id : int
        Unique identifier for the job.
    name : str
        Name of the job, e.g. Sample name
    tasks : list
        List of Task objects belonging to the job.

    Methods
    -------
    add_task(task)
        Appends the task to the list of tasks
    """
    def __init__(self, job_id, name):
        self.job_id = job_id
        self.name = name
        self.tasks = []

    def add_task(self, task):
        """
        Adds a task to the job.

        Parameters
        ----------
        task : Task
            Task object to be added.
        """
        self.tasks.append(task)

class Batch:
    """
    Class representing a batch of jobs in the job shop scheduling problem.

    Attributes
    ----------
    num_reactors :
        Number of reactors available.
    horizon : int
        Horizon for the scheduling problem - i.e. longest possible end time
    jobs : list
        List of Job objects in the batch.
    model : cp_model.CpModel
        Constraint programming model for the batch.
    """
    def __init__(self, num_reactors, horizon):
        self.num_reactors = num_reactors
        self.horizon = horizon
        self.jobs = []
        self.model = cp_model.CpModel()

    def add_job(self, job):
        """
        Adds a job to the batch.

        Parameters
        ----------
        job : Job
            Job object to be added.
        """
        self.jobs.append(job)

def find_tasks_using_resource(batch, resource):
    """
    Finds tasks in the batch that use the specified resource.

    Parameters
    ----------
    batch : Batch
        Batch object containing jobs and tasks.
    resource : int
        Resource ID to search for.

    Returns
    -------
    tasks : list
        List of Task objects using the specified resource.
    """
    tasks = []
    for job in batch.jobs:
        for task in job.tasks:
            if "dry" not in task.name:
                if task.resource == resource:
                    tasks.append(task)
            elif "dry" in task.name:
                for i, r in enumerate(task.resource):
                    if r == resource:
                        tasks.append(task)
    return tasks

def find_tasks_of_type(batch, task_name):
    """
    Finds tasks in the batch that match the specified task name.

    Parameters
    ----------
    batch : Batch
        Batch object containing jobs and tasks.
    task_name : str
        Task name to search for.

    Returns
    -------
    tasks : list
        List of Task objects matching the specified task name.
    """
    tasks = []
    for job in batch.jobs:
        for task in job.tasks:
            if task_name in task.name:
                tasks.append(task)
    return tasks

def find_tasks_resource_type(batch, task_name, resource):
    """
    Finds tasks in the batch that match the specified task name AND resource.

    Parameters
    ----------
    batch : Batch
        Batch object containing jobs and tasks.
    task_name : str
        Task name to search for.
    resource : int
        Resource ID to search for.

    Returns
    -------
    tasks : list
        List of Task objects matching the specified task name AND resource.
    """
    tasks = []
    for job in batch.jobs:
        for task in job.tasks:
            if task_name in task.name:
                if task.resource == resource:
                    tasks.append(task)
    return tasks

def find_intervals_using_resource(batch, resource):
    """
    Finds interval variables in the batch that use the specified resource.

    Parameters
    ----------
    batch : Batch
        Batch object containing jobs and tasks.
    resource : int
        Resource ID to search for.

    Returns
    -------
    intervals : list
        List of interval variables using the specified resource.
    """
    intervals = []
    for job in batch.jobs:
        for task in job.tasks:
            if "dry" not in task.name:
                if task.resource == resource:
                    intervals.append(task.interval_var)
            elif "dry" in task.name:
                for i, r in enumerate(task.resource):
                    if r == resource:
                        intervals.append(task.interval_var[i])

    return intervals

def find_intervals_of_task(batch, task_name):
    """
    Finds interval variables in the batch that correspond to tasks with the specified name.

    Parameters
    ----------
    batch : Batch
        Batch object containing jobs and tasks.
    task_name : str
        Task name to search for.

    Returns
    -------
    intervals : list
        List of interval variables corresponding to tasks with the specified name.
    """
    intervals = []
    for job in batch.jobs:
        for task in job.tasks:
            if task_name in task.name:
                intervals.append(task.interval_var)
    return intervals

def find_intervals_resource_task(batch, task_name, resource):
    """
    Finds interval variables in the batch that correspond to tasks with the specified name and resource.

    Parameters
    ----------
    batch : Batch
        Batch object containing jobs and tasks.
    task_name : str
        Task name to search for.
    resource : int
        Resource ID to search for.

    Returns
    -------
    intervals : list
        List of interval variables corresponding to tasks with the specified name and resource.
    """
    intervals = []
    for job in batch.jobs:
        for task in job.tasks:
            if "dry" not in task.name:
                if task_name in task.name:
                    if task.resource == resource:
                        intervals.append(task.interval_var)
            elif "dry" in task.name:
                if task_name in task.name:
                    for i, r in enumerate(task.resource):
                        if r == resource:
                            intervals.append(task.interval_var[i])
    return intervals


def solve_job_shop_schedule(unit_ops_df, num_reactors, plot = False):
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

    #Collect a list of all the samples
    samples = unit_ops_df["Sample Name"].unique().tolist()

    #Find the niave time for the batch of experiments (simple sum of all durations)
    horizon = int(np.sum(np.ceil(unit_ops_df["Duration (Ds)"])))

    #Create Batch object for the experiment and populate the Jobs and Tasks
    batch = Batch(num_reactors=num_reactors, horizon=horizon)
    for i, sample in enumerate(samples):
        job = Job(job_id= i, name = sample)

        sub_df = unit_ops_df[unit_ops_df["Sample Name"] == sample]

        for j in sub_df.index:
            task = Task(task_id=j,
                        name = sub_df.loc[j, "UnitOP"],
                        duration= sub_df.loc[j, "Duration (Ds)"],
                        reactor = sub_df.loc[j, "Reactor"],
                        reactor_temp = sub_df.loc[j, "Reactor Temperature (C)"])
            task.assign_resouce(batch.num_reactors)
            task.create_interval_var(batch.model, batch.horizon)
            job.add_task(task)

        batch.add_job(job)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Applying all the constraints for the job shop problem
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    #Find all the tasks using the Arm&Clamp, and impose no_overlap constraint
    arm_intervals = find_intervals_using_resource(batch, 0)
    batch.model.add_no_overlap(arm_intervals)

    #For each sample the ops must happen in order
    for job in batch.jobs:
        for i, task in enumerate(job.tasks):
            if i != 0:
                if "dry" not in task.name:
                    batch.model.add(job.tasks[i-1].end_var <= task.start_var)

                elif "dry" in task.name:
                    for alt_task_start in task.start_var:
                        batch.model.add(job.tasks[i-1].end_var <= alt_task_start)

    #Constrain the bool_vars for the "dry" tasks so each sample can only choose one
    for job in batch.jobs:
        for task in job.tasks:
            if "dry" in task.name:
                batch.model.AddExactlyOne(task.bool_vars)

    #Impose the capacity contraint on for the reactors
    for i in range(batch.num_reactors):
        m = i + 1 #Convert index to resouce ID
        interval_list = find_intervals_using_resource(batch, m)
        batch.model.AddCumulative(interval_list,
                                [1]*len(interval_list),
                                4,
                                )

    #No Overlap between reacting and drying on the same machine
    for i in range(batch.num_reactors):
        m = i + 1 #Convert index to resouce ID
        react_list = find_intervals_resource_task(batch, "react", m)
        dry_list = find_intervals_resource_task(batch, "dry", m)

        for exclusive_intervals in itertools.product(react_list, dry_list):
            batch.model.add_no_overlap(list(exclusive_intervals))

    #Impose capacity constraint for centrifuge tasks
    cent_intervals = find_intervals_of_task(batch, "centrifuge")
    batch.model.AddCumulative(cent_intervals,
                            [1]*len(cent_intervals),
                            6,
                            )

    #If the centrifuge tasks overlap, then the start times should be equal, otherwise they should not overlap
    cent_tasks = find_tasks_of_type(batch, "centrifuge")
    for i, cent_a in enumerate(cent_tasks):
        for j, cent_b in enumerate(cent_tasks):
            if i < j:
                
                b = batch.model.NewBoolVar(f"centrifuge_overlap_{cent_a.name}_{cent_b.name}")
                b_order = batch.model.NewBoolVar(f"centrifuge_order_{cent_a.name}_{cent_b.name}")
        
                batch.model.Add(cent_a.start_var == cent_b.start_var).OnlyEnforceIf(b)
            
                batch.model.Add(cent_a.end_var <= cent_b.start_var).OnlyEnforceIf(~b, b_order)
                batch.model.Add(cent_b.end_var <= cent_a.start_var).OnlyEnforceIf(~b, ~b_order)

    #Impose capacity constraint for sonicate tasks
    sonicate_intervals = find_intervals_of_task(batch, "sonicate")
    batch.model.AddCumulative(sonicate_intervals,
                            [1]*len(sonicate_intervals),
                            3,
                            )

    # Add_fluids.end should be within 42 Ds of react.start for each sample
    for job in batch.jobs:
        add_fluids = None
        react = None
        for task in job.tasks:
            if "add_fluids" in task.name:
                add_fluids = task.end_var
            elif "react" in task.name:
                react = task.start_var
        if (add_fluids is not None) and (react is not None):
            batch.model.add(add_fluids + 42 > react)

    for i in range(batch.num_reactors):
        m = i + 1 #Convert index to resource ID
        react_tasks = find_tasks_resource_type(batch, "react", m)
        temperatures = []
        durations = []
        for task in react_tasks:
            temperatures.append(task.reactor_temp)
            durations.append(task.duration)
        unique_temps = np.unique(temperatures)
        longest_task_duration_at_each_temp = []
        for temp in unique_temps:
            indexes = np.where(temperatures == temp)[0]
            task_at_temp = np.array(react_tasks)[indexes]

            for i, task_i in enumerate(task_at_temp):
                for j, task_j in enumerate(task_at_temp):
                    if i < j:
                        batch.model.add(task_i.end_var == task_j.end_var)
            
            durations_at_temp = np.array(durations)[indexes]
            longest_task_duration_at_each_temp.append(task_at_temp[np.argmax(durations_at_temp)])

        if len(longest_task_duration_at_each_temp) > 1:
            for i, task_i in enumerate(longest_task_duration_at_each_temp[:-1]):
                task_j = longest_task_duration_at_each_temp[i+1]

                batch.model.add(task_i.end_var <= task_j.start_var)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Creating objective for the job shop problem
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Makespan objective.
    obj_var = batch.model.new_int_var(0, horizon, "makespan")

    #Gather all the end times
    all_end_list = []
    for job in batch.jobs:
        for task in job.tasks:
            if "dry" not in task.name:
                all_end_list.append(task.end_var)
            elif "dry" in task.name:
                for option_end in task.end_var:
                    all_end_list.append(option_end)

    #Add the max_equality constraint
    batch.model.add_max_equality(obj_var, all_end_list)
    batch.model.minimize(obj_var)

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
    status = solver.solve(batch.model)

    print("solver status", solver.status_name(status))

    # ~~~~~~~~~~~~~~~~~~~
    # Record the solution
    # ~~~~~~~~~~~~~~~~~~~

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:

        unit_ops_df["Start Time (Ds)"] = "?"
        unit_ops_df["End Time (Ds)"] = "?"

        for job in batch.jobs:
            sample_name = job.name
            for task in job.tasks:
                task_name = task.name
                unit_op_table_index = unit_ops_df[(unit_ops_df["Sample Name"] == sample_name) &
                                                (unit_ops_df["UnitOP"] == task_name)].index.values[0]
                if "dry" not in task_name:
                    unit_ops_df.loc[unit_op_table_index, "Start Time (Ds)"] = solver.value(task.start_var)
                    unit_ops_df.loc[unit_op_table_index, "End Time (Ds)"] = solver.value(task.end_var)

                elif "dry" in task_name:
                    bool_values = solver.values(task.bool_vars)
                    index = np.where(bool_values)[0][0]

                    unit_ops_df.loc[unit_op_table_index, "Reactor"] = index # index is reactor (not resource) index
                    unit_ops_df.loc[unit_op_table_index, "Start Time (Ds)"] = solver.value(task.start_var[index])
                    unit_ops_df.loc[unit_op_table_index, "End Time (Ds)"] = solver.value(task.end_var[index])

                    
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


