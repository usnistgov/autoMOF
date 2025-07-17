

import numpy as np
import pandas as pd

import plotly.express as px

from drmxlt_MOF.op_scheduler import add_unit_ops_resource_collumn



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

    unit_ops_df = add_unit_ops_resource_collumn(unit_ops_df)


    #Gantt Chart Per Unit OP
    fig1 = px.bar(unit_ops_df, 
             x="Duration (Ds)", 
             base="Start Time (Ds)", 
             y="Step", 
             orientation="h", 
             color="Step")
    
    # Update layout for better visualization
    fig1.update_layout(title="Unit OP Timeline", xaxis_title="Time (Ds)", yaxis_title="Unit OP")


    #Gantt Chart Per Resource
    fig2 = px.bar(unit_ops_df.fillna("None"), 
             x="Duration (Ds)", 
             base="Start Time (Ds)", 
             y="Resource", 
             orientation="h", 
             barmode="group",
             color="Sample Name")
    
    # Update layout for better visualization
    fig2.update_layout(title="Resource Timeline", xaxis_title="Time (Ds)", yaxis_title="Resource")

    #Gantt Chart Per Sample
    fig3 = px.bar(unit_ops_df.fillna("None"), 
                x="Duration (Ds)", 
                base="Start Time (Ds)", 
                y="Sample Name", 
                orientation="h", 
                color="UnitOP")

    # Update layout for better visualization
    fig3.update_layout(title="Sample Timeline", xaxis_title="Time (Ds)", yaxis_title="Sample Name")


    if write_to_file == True:
        fig1.write_image(f"{write_directory}/UnitOP_schedule_{filename_suffix}.png")
        fig2.write_image(f"{write_directory}/Resource_schedule_{filename_suffix}.png")
        fig3.write_image(f"{write_directory}/Sample_schedule_schedule_{filename_suffix}.png")

    return fig1, fig2, fig3
