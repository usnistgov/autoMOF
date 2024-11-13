from north import NorthC9  # import the class to communicate with the C9 controller
from Locator import *  # import the contents of the Locator table (View -> Locator)
from system_state_tools import find_vial, find_liquid, check_stock_solution
c9 = NorthC9('A',network_serial="AU06D2C0")  # instantiate a C9 controller object with C9 network address A-

#dispense the full volume of a syringe pump

def max_dispense(pump_num):
    #Dispense the maximum volume of this pump.
    dispense(pump_num, c9.pumps[pump_num]['volume'])
 
#general dispense function

#will dispense 10mL with 2 strokes given 5mL syringe

def dispense(pump_num, ml_remaining):
    
    #Dispense max volumes at a time until the remaining volume is less than the max.
    while ml_remaining > c9.pumps[pump_num]['volume']:

        max_dispense(pump_num)

        c9.delay(0.2)

        ml_remaining -= c9.pumps[pump_num]['volume']
    
    #Once the remaining volume is less than the max:
    #Draw the solution into the syringe
    c9.set_pump_valve(pump_num, c9.PUMP_VALVE_LEFT)
    c9.aspirate_ml(pump_num, ml_remaining)
    
    #wait
    c9.delay(0.2)
    
    #Dispense from the syringe into the vial
    c9.set_pump_valve(pump_num, c9.PUMP_VALVE_RIGHT)
    c9.dispense_ml(pump_num, ml_remaining)
 

def fill_vial(vial_id, liquid, volume):
    """Fill a vial with a volume of a liquid"""
    
    #Set default movement velocity
    c9.default_vel=20

    #look-up current location of vial
    vial_location = find_vial(vial_id)
    
    #look-up the liquid pump id
    pump_id, carousel_position = find_liquid(liquid)
    
    #Check if there's enough stock solution
    enough_stock = check_stock_solution(pump_id, volume)
    
    if enough_stock:
        #Go to that location and grab the vial
        c9.goto_safe(vial_location)
        c9.close_gripper()
        
        #Go to the clamp, uncap, and move the arm out of the way
        c9.goto_xy_safe(clamp)
        c9.move_z(181)#go to 11100
        c9.close_clamp()
        c9.uncap() #2mm/rev and 2 revs to remove cap  Uncapped at 10600=186
        c9.goto_safe(home) #hold on to the cap and move it to home
        #TODO: update vial location in database
        
        #Move the carousel into position
        c9.move_carousel(carousel_position,17)
        
        #Tare the scale
        tare_scale() #leaves the clamp open
        
        #Dispense the requested volume of liquid
        dispense(pump_id,volume)
        
        #Measure how much was despensed
        mass_liquid = c9.read_steady_scale()
        #TODO: update vial information in database
        
        #Move the carousel out of the way
        c9.move_carousel(0,0)
        
        #Bring the cap back, and re-cap
        c9.goto_xy_safe(clamp)
        c9.close_clamp()
        c9.move_z(186)
        c9.cap(revs=2,torque_thresh=1750)
        c9.open_clamp()
        
        #Bring the vial back
        c9.goto_safe(vial_location) #same location it started with 
        c9.open_gripper()
        #TODO: update vial location in database
        
        #Move the arm back home
        c9.goto_safe(home)
        
        
    else:
        print(f"Not enough stock of {liquid}")
        
def tare_scale():
    #Open the clamp so that the vial rests on the scale
    c9.open_clamp()
    
    #Tare, ensuring steady state:
    c9.zero_scale()
    while c9.read_steady_scale() != 0:
        c9.zero_scale()
