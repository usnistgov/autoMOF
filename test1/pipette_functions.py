import numpy as np



"""Make an array of indexes for the pippette tips
In the shape of how they are set up on the robot 3 rows of 16 tips.
row 0 is closest to the base of the arm
row 2 is closest to the door
column 0 furthest from the arm
column 15 is closest to the arm"""
pipette_array = np.arange(0,48).reshape(-1,3).T #Array 0-48, 3x16, but rows are out of order.
pipette_array = pipette_array[::-1, :] # Flip the ordering of the rows. 
pipette_array = np.flip(pipette_array, axis = 1) # Flip the ordering of the columns to match how they are layed out on the robot.

pipette_order = [i for i in range(2, 48, 3)] \
                + [i for i in range(1, 48, 3)] \
                + [i for i in range(0, 48, 3)]
########### NEED to refactor to use pipette_order #################

def fresh_pipette_rack(empty_pipette_indexes = []):
    """Create an array that shows where there are fresh pipettes.
    If any indexes are empty, enter those as a list, 
    e.g. empty_pipette_indexes = [0, 10, 43]"""

    fresh_pipettes = np.ones_like(pipette_array)

    for i in empty_pipette_indexes:
        position = np.where(pipette_array == i)
        fresh_pipettes[position] = 0

    return fresh_pipettes


def get_next_pipette_tip(pipette_array, fresh_pipettes):
    """Find the next available fresh pipette tip,
    go there grab it, and mark that it's being used."""

    #Find the next available fresh pipette index
    next_pipette = np.min(pipette_array[fresh_pipettes == 1])

    #Pick up that pipette tip
    c.goto_safe(p_up[next_pipette])
    c.goto_safe(p_up_wp)

    #Mark that that pipette tip index is used
    fresh_pipettes[pipette_array == next_pipette] = 0

    #Push the fresh pipette information to the database
    #TODO

    return pipette_array, fresh_pipettes


