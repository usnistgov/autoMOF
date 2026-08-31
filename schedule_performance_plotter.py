import json
import numpy as np

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


#Read in scheduling performance scaling at decasecond resolution
with open("performance_table_das.json", "r") as file:
    das_data = json.load(file)


number_samples_das = das_data.keys()

das_compute_times = []
das_naive_times = []
das_scheduled_times = []
for key in number_samples_das:
    compute_time = das_data[key]["Time to compute (s)"]
    das_compute_times.append(compute_time)

    niave_time = das_data[key]["Naive time (Ds)"]
    das_naive_times.append(niave_time)

    scheduled_time = das_data[key]["Scheduled time (Ds)"]
    das_scheduled_times.append(scheduled_time)


das_speedups = np.array(das_naive_times)/np.array(das_scheduled_times)

number_samples_das = np.array(list(number_samples_das))
number_samples_das = number_samples_das.astype(int)

#Read in scheduling performance scaling at hectosecond resolution
with open("performance_table_hs.json", "r") as file:
    hs_data = json.load(file)


number_samples_hs = hs_data.keys()

hs_compute_times = []
hs_naive_times = []
hs_scheduled_times = []
for key in number_samples_hs:
    compute_time = hs_data[key]["Time to compute (s)"]
    hs_compute_times.append(compute_time)

    niave_time = hs_data[key]["Naive time (hs)"]*10 #convert from hs to das
    hs_naive_times.append(niave_time)

    scheduled_time = hs_data[key]["Scheduled time (hs)"]*10 #convert from hs to das
    hs_scheduled_times.append(scheduled_time)


hs_speedups = np.array(hs_naive_times)/np.array(hs_scheduled_times)

number_samples_hs = np.array(list(number_samples_hs))
number_samples_hs = number_samples_hs.astype(int)


#Read in scheduling performance scaling at decasecond resolution with a time budget
with open("performance_table_tb.json", "r") as file:
    tb_data = json.load(file)


number_samples_tb = tb_data.keys()

tb_compute_times = []
tb_naive_times = []
tb_scheduled_times = []
for key in number_samples_tb:
    compute_time = tb_data[key]["Time to compute (s)"]
    tb_compute_times.append(compute_time)

    niave_time = tb_data[key]["Naive time (Ds)"]
    tb_naive_times.append(niave_time)

    scheduled_time = tb_data[key]["Scheduled time (Ds)"]
    tb_scheduled_times.append(scheduled_time)


tb_speedups = np.array(tb_naive_times)/np.array(tb_scheduled_times)

number_samples_tb = np.array(list(number_samples_tb))
number_samples_tb = number_samples_tb.astype(int)



compute_dataset = [(number_samples_das, das_compute_times, das_scheduled_times, das_speedups, "das"),
                   (number_samples_hs, hs_compute_times, hs_scheduled_times, hs_speedups, "hs"),
                   (number_samples_tb, tb_compute_times, tb_scheduled_times, tb_speedups, "tb")]



fig = make_subplots(rows = 1, cols = 3, subplot_titles = ("Compute Scaling", "Scheduled Time", "Speedup"))

for i, (x, y_compute, y_schedule, y_speed, label) in enumerate(compute_dataset):
    # color = i + 1
    color = px.colors.qualitative.Plotly[i]

    fig.add_trace(
        go.Scatter(x = x,
                   y = y_compute,
                   mode = "lines+markers",
                   line = dict(color = color),
                   name = label,
                   legendgroup = label,
                   showlegend = True),
        row = 1,
        col = 1
        )

    fig.add_trace(
        go.Scatter(x = x,
                   y = y_schedule,
                   mode = "lines+markers",
                   line = dict(color = color),
                   name = label,
                   legendgroup = label,
                   showlegend = False),
        row = 1,
        col = 2
        )
    
    fig.add_trace(
        go.Scatter(x = x,
                   y = y_speed,
                   mode = "lines+markers",
                   line = dict(color = color),
                   name = label,
                   legendgroup = label,
                   showlegend = False),
        row = 1,
        col = 3
        )

fig.update_yaxes(type = "log", row = 1, col = 1)
fig.update_xaxes(title_text="Number of Samples", row=1, col=1)
fig.update_xaxes(title_text="Number of Samples", row=1, col=2)
fig.update_xaxes(title_text="Number of Samples", row=1, col=3)
fig.update_yaxes(title_text="Time (s)", row=1, col=1)
fig.update_yaxes(title_text="Scheduled Time (das)", row=1, col=2)
fig.update_yaxes(title_text="Speedup", row=1, col=3)

fig.show()
