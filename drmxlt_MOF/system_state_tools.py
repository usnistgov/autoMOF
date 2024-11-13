"""Helping functions to interact with the databases
that keep track of the state of vials/samples
and state of the system"""



def find_vial(vial_id):
    """Look up the vial in the sample state database
    and find its location."""
    
    #TODO
    
    return location
    
def find_liquid(liquid):
    """Look up in the system state database
    and find what pump the liquid is at"""
    
    #TODO
    
    
    return pump_id, carousel_position


def check_stock_solution(pump_id, volume):
    """Look up in the system state database
    if there is enough stock in the resevour."""
    
    #TODO
    
    #Is the current_volume greater than the requested volume?
    enough_volume = current_volume > volume
    
    return enough_volume


    