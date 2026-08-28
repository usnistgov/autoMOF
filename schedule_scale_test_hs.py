import time


import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

import numpy as np
import json

from src.op_scheduler_hs import create_unit_ops_df, assign_reactors, solve_job_shop_schedule, interleave_reactor_preheating
from src.experiments import Ternary_colordemo, Cu_BTC
from src.schedule_plotter import plot_gantt_chart

from src.op_scheduler_hs import add_unit_ops_resource_collumn


seed = 42
num_reactors = 2

results = {}

for i in range(1,21):
    example = Cu_BTC(initial_samples = i, batch_size = 4)
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

    results[i] = {"Time to compute (s)": elapsed_time,
                    "Naive time (hs)": unit_ops_df["Duration (hs)"].sum(),
                    "Scheduled time (hs)": unit_ops_df["End Time (hs)"].to_numpy()[-1]}
    print(results[i])


    with open("performance_table_hs.json", "w") as json_file:
        json.dump(results, json_file)