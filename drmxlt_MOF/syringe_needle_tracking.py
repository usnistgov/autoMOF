

import numpy as np

# from drmxlt_MOF.Locator import *
from Locator import *

#An array of showing how the indexes of the needles are aranged on the robot
needle_array = np.arange(0,48).reshape(-1,3).T #Array 0-48, 3x16, but rows are out of order.
needle_array = needle_array[::-1, :] # Flip the ordering of the rows.
needle_array = np.flip(needle_array, axis = 1) # Flip the ordering of the columns to match how they are layed out on the robot.

#An array showing the order in which the needles should be picked up
needle_order = np.array([i for i in range(2, 48, 3)] \
                + [i for i in range(1, 48, 3)] \
                + [i for i in range(0, 48, 3)])


def fresh_needle_rack(empty_needle_indexes = []):
    """Create an array that shows where there are fresh needles.
    If any indexes are empty, enter those as a list,
    e.g. empty_needle_indexes = [0, 10, 43]
    
    Parameters
    ----------
    empty_needle_indexes : list
        List of which indexes in the needle array are empty
        
    Returns
    -------
    fresh_needles
        nd.array showing 1 for where there are fresh needles and 0 for empty
    """

    fresh_needles = np.ones_like(needle_array)

    for i in empty_needle_indexes:
        position = np.where(needle_array == i)
        fresh_needles[position] = 0

    return fresh_needles



def get_next_needle_tip(system_db, c):
    """
    Find the next available fresh syringe needle,
    go there grab it, and mark that it's being used.
    
    Parameters
    ----------
    system_db : dict (-like)
        Database that tracks all the status of all components of the system
    c : NorthC9
        NorthC9 object for instrument control
    """

    #Mask off the used needles
    mask = [x in system_db["needle_array"][system_db["fresh_needles"] == 1]  for x in system_db["needle_order"]]

    #Find the next (as per the needle_order) available fresh needle
    next_needle = system_db["needle_order"][mask][0]
    
    # #Pick up that needle tip
    c.goto_safe(p_up[next_needle])
    c.goto_safe(p_up_wp)

    #Mark that that needle tip index is used
    system_db["fresh_needles"][system_db["needle_array"] == next_needle] = 0
    #TODO: push system db to Cordra

def sn_rem(c):
    """
    Remove a syringe needle
    
    Parameters
    ----------
    c : NorthC9
        NorthC9 object for instrument control
    """
    c.goto_safe(p_remover_ap)
    c.goto(p_rem,vel=5,accel=5)
    c.move_z(292)


fresh_needles = fresh_needle_rack()