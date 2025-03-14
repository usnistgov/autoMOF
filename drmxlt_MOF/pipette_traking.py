

import numpy as np

pipette_array = np.arange(0,48).reshape(-1,3).T #Array 0-48, 3x16, but rows are out of order.
pipette_array = pipette_array[::-1, :] # Flip the ordering of the rows.
pipette_array = np.flip(pipette_array, axis = 1) # Flip the ordering of the columns to match how they are layed out on the robot.

pipette_order = np.array([i for i in range(2, 48, 3)] \
                + [i for i in range(1, 48, 3)] \
                + [i for i in range(0, 48, 3)])


def fresh_pipette_rack(empty_pipette_indexes = []):
    """Create an array that shows where there are fresh pipettes.
    If any indexes are empty, enter those as a list,
    e.g. empty_pipette_indexes = [0, 10, 43]"""

    fresh_pipettes = np.ones_like(pipette_array)

    for i in empty_pipette_indexes:
        position = np.where(pipette_array == i)
        fresh_pipettes[position] = 0

    return fresh_pipettes



def get_next_pipette_tip(pipette_order, pipette_array, fresh_pipettes):
    """Find the next available fresh pipette tip,
    go there grab it, and mark that it's being used."""

    #Mask off the used pipettes
    mask = [x in pipette_array[fresh_pipettes == 1]  for x in pipette_order]

    #Find the next (as per the pipette_order) available fresh pipette
    next_pipette = pipette_order[mask][0]
    print(next_pipette)

    # #Pick up that pipette tip
    # c.goto_safe(p_up[next_pipette])
    # c.goto_safe(p_up_wp)

    #Mark that that pipette tip index is used
    fresh_pipettes[pipette_array == next_pipette] = 0

    #Push the fresh pipette information to the database
    #TODO

    return fresh_pipettes

fresh_pipette = fresh_pipette_rack()