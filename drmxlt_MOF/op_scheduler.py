import numpy as np
import pandas as pd


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
    total_react_duration.append(np.max(unit_ops_df[unit_ops_df["UnitOP"]=='react'][temp_mask]["Reactor Duration (Ds)"]))
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
