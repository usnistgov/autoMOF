

import numpy as np
import pandas as pd

import plotly.express as px
from plotly.subplots import make_subplots


def plot_gantt_chart(unit_ops_df, write_to_file = False, write_directory = None, filename_suffix = None):
    """"
    Function for plotting Gantt charts of the unit ops schedule.
    From the perspective of:
    1. Each unit op
    2. Each resource
    3. Each sample
    
    Parameters
    ----------
    unit_ops_df : DataFrame
        pd.DataFrame of the schedule of all the unit ops
    write_to_file : bool
        Flag for whether or not to write the images to file
    write_directory : str
        String for the file directory
    filename_suffix : str
        String to tack onto the end of the filename to create unique filenames. 

    Returns
    -------
    fig1 : figure
        plotly figure of Gantt chart per unit op
    fig2 : figure
        plotly figure of Gantt chart per resource
    fig3 : figure
        plotly figure of Gantt chart per sample

    """


    #Gantt Chart Per Unit OP
    fig1 = px.bar(unit_ops_df, 
             x="Duration (Ds)", 
             base="Start Time (Ds)", 
             y="Step", 
             orientation="h", 
             color="Step",
             color_continuous_scale=px.colors.sequential.Viridis,
             template = "simple_white",
             width = 1200,
             height = 800)
    
    # Update layout for better visualization
    fig1.update_layout(title="Unit OP Timeline", xaxis_title="Time (Ds)", yaxis_title="Unit OP",
                       xaxis=dict(tickformat=".3r"))


    #Gantt Chart Per Resource
    n_colors = len(unit_ops_df["Sample Name"].unique())
    colors = px.colors.sample_colorscale("viridis", [n/(n_colors -1) for n in range(n_colors)])
    fig2 = px.bar(unit_ops_df.replace(np.nan, "None"), # unit_ops_df.fillna("None") 
             x="Duration (Ds)", 
             base="Start Time (Ds)", 
             y="Resource", 
             orientation="h", 
             barmode="group",
             color="Sample Name",
             color_discrete_sequence=colors,
             template = "simple_white",
             width = 1200,
             height = 800)
    
    # Update layout for better visualization
    fig2.update_layout(title="Resource Timeline", xaxis_title="Time (Ds)", yaxis_title="Resource",
                       xaxis=dict(tickformat=".3r"),
                       font=dict(size=24),
                       legend_font_size=24)
    fig2.update_xaxes(tickfont=dict(size=24))
    fig2.update_xaxes(title_font_size=28)
    fig2.update_yaxes(tickfont=dict(size=24))
    fig2.update_yaxes(title_font_size=28)

    #Gantt Chart Per Sample
    n_colors = len(unit_ops_df["UnitOP"].unique())
    colors = px.colors.sample_colorscale("plasma", [n/(n_colors -1) for n in range(n_colors)])
    fig3 = px.bar(unit_ops_df.replace(np.nan, "None"), # unit_ops_df.fillna("None"), 
                x="Duration (Ds)", 
                base="Start Time (Ds)", 
                y="Sample Name", 
                orientation="h", 
                color="UnitOP",
                color_discrete_sequence=colors,
                template = "simple_white",
                width = 1200,
                height = 800)

    # Update layout for better visualization
    fig3.update_layout(title="Sample Timeline", xaxis_title="Time (Ds)", yaxis_title="Sample Name",
                       xaxis=dict(tickformat=".3r"),
                       font=dict(size=24),
                       legend_font_size=24)
    fig3.update_xaxes(tickfont=dict(size=24))
    fig3.update_xaxes(title_font_size=28)
    fig3.update_yaxes(tickfont=dict(size=24))
    fig3.update_yaxes(title_font_size=28)


    if write_to_file == True:
        fig1.write_image(f"{write_directory}/UnitOP_schedule_{filename_suffix}.pdf")
        fig2.write_image(f"{write_directory}/Resource_schedule_{filename_suffix}.pdf")
        fig3.write_image(f"{write_directory}/Sample_schedule_schedule_{filename_suffix}.pdf")

    return fig1, fig2, fig3 