import time


import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

import numpy as np


from drmxlt_MOF.op_scheduler_dev_2 import create_unit_ops_df, assign_reactors, solve_job_shop_schedule, interleave_reactor_preheating
from drmxlt_MOF.experiments import Ternary_colordemo, Cu_BTC
from drmxlt_MOF.schedule_plotter import plot_gantt_chart

from drmxlt_MOF.op_scheduler_dev_2 import add_unit_ops_resource_collumn

seed = 42
# seed = 41
np.random.seed(seed)

example = Cu_BTC(initial_samples = 16, batch_size = 4)

num_reactors = 2

unit_ops_df, op_order = create_unit_ops_df(example.sample_db, 
                                 True, # Add fluids
                                 True, # React
                                 3, # Wash_Cycles
                                 True, # Dry
                                 
                                 
                                 False, # Independent Centrifuge step
                                 False, # Independent Remove_supernatent step
                                 False, # Independent Sonicate step
                                 )

unit_ops_df, reactor_df = assign_reactors(unit_ops_df, num_reactors, 4)

start_time = time.time()
unit_ops_df = solve_job_shop_schedule(unit_ops_df, num_reactors)
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Elapsed time for scheduling: {elapsed_time:.6f} seconds")

unit_ops_df = interleave_reactor_preheating(unit_ops_df, 5)

write_directory = "C:/Users/drmxlt/Documents/Orchestrator Paper/"
suffix = "initial_batch"
fig1, fig2, fig3 = plot_gantt_chart(unit_ops_df, True, write_directory, suffix)
fig1.show()
fig2.show()
fig3.show()

niave_time = unit_ops_df["Duration (Ds)"].sum() #Ds
niave_time *= 10 # s
niave_time *= 1/60 #mins
niave_time *= 1/60 #hours
niave_time *= 1/24 #days
print("niave_time (days) =", niave_time)

end_time = unit_ops_df["End Time (Ds)"].max()
end_time *= 10 # s
end_time *= 1/60 #mins
end_time *= 1/60 #hours
end_time *= 1/24 #days
print("end_time (days) =", end_time)

mask = unit_ops_df["Start Time (Ds)"] < 40000
unit_ops_df.loc[mask,"Status"] = "Completed"

sub_df = unit_ops_df[unit_ops_df["Status"] == "To Do"]
sub_sub_df = sub_df[["index", "Sample Name", "UnitOP", "Duration (Ds)", "Reactor", "Reactor Temperature (C)", "Status"]]

example_2 = Cu_BTC(initial_samples = 8, batch_size = 4)

new_ops_df, op_order_2 = create_unit_ops_df(example_2.sample_db, 
                                 True, # Add fluids
                                 True, # React
                                 3, # Wash_Cycles
                                 True, # Dry
                                 
                                 
                                 False, # Independent Centrifuge step
                                 False, # Independent Remove_supernatent step
                                 False, # Independent Sonicate step
                                 )

new_ops_df, reactor_df = assign_reactors(new_ops_df, num_reactors, 4)

next_batch_ops_df = pd.concat([sub_sub_df, new_ops_df], ignore_index=True)

start_time = time.time()
next_batch_ops_df = solve_job_shop_schedule(next_batch_ops_df, num_reactors)
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Elapsed time for re-scheduling: {elapsed_time:.6f} seconds")

next_batch_ops_df = interleave_reactor_preheating(next_batch_ops_df, 5)

write_directory = "C:/Users/drmxlt/Documents/Orchestrator Paper/"
suffix = "re-schedule"
fig1a, fig2a, fig3a = plot_gantt_chart(next_batch_ops_df, True, write_directory, suffix)
fig1a.show()
fig2a.show()
fig3a.show()

