c=None
from Locator import *

#dictionary of carusel positions to dispence to the clamp
pump_c_pos = {5: 45, 4: 90, 3:135}

#dispense the full volume of a syringe pump

def max_dispense(pump_num):

    dispense(pump_num, c.pumps[pump_num]['volume'])
 
#general dispense function

#will dispense 10mL with 2 strokes given 5mL syringe

def dispense(pump_num, ml_remaining):

    while ml_remaining > c.pumps[pump_num]['volume']:

        max_dispense(pump_num)

        c.delay(0.2)

        ml_remaining -= c.pumps[pump_num]['volume']

    c.set_pump_valve(pump_num, c.PUMP_VALVE_RIGHT)

    c.aspirate_ml(pump_num, ml_remaining)

    c.delay(0.2)

    c.set_pump_valve(pump_num, c.PUMP_VALVE_LEFT)

    c.dispense_ml(pump_num, ml_remaining)
 
def tare_balance():
    c.zero_scale()
    while c.read_steady_scale() != 0:
        c.delay(.2)
        c.zero_scale()
        
        

"""Order of pipette tips 3 rows of 16 for total of 48
# front row
# middle row
# back row """
########### TODO: refactor so that the pipette tips are organized in a 2D array, with states 0 for empty, 1 for pipette tip, 2 for syringe 
pipette_order = [i for i in range(2, 48, 3)] \
                + [i for i in range(1, 48, 3)] \
                + [i for i in range(0, 48, 3)] 

next_pip_i = -1 #Global index of pipette tips to load starting from the front-right 
def next_pipette():
    global next_pip_i
    next_pip_i += 1
    return pipette_order[next_pip_i]
 
#c9.goto_safe(p_up[next_pipette])

def pip_get(ind=None):
    """funtion to get the pipette tip"""
    if ind is None:
        ind = next_pipette()
    c.goto_safe(p_up[ind])
    c.goto_safe(p_up_wp) #pipett way point to avoid collisions
    
def pip_rem():
    """function to remove the pipette tip"""
    c.goto_safe(p_remover_ap)
    c.goto(p_rem,vel=5,accel=5)
    c.move_z(292)
    
def vortex(time=30,vel=50,amp=1000):
    """function so "stir" the stuff in the vial"""
    dis=vel*1000*time
    print(dis)
    vt=c.move_axis(0,dis,vel=vel,wait=0)
    elbow_pos = c.get_axis_position(1)
    while not vt.is_done():
        c.move_axis(1, elbow_pos+amp,vel=30,accel=30)
        c.move_axis(1, elbow_pos-amp,vel=30,accel=30)
    c.reduce_axis_position(0)


def pipette(vol=.5, source=p_rack_right[5], source_height = 130):
    """funtion that gets pipette tip, and pipettes some liquid to (the implied vial in) the clamp 
    from the source vial"""
    if vol>.9:
        raise ValueError("pipette volume too large for tip/syringe")
    c.move_pump(0,0)
    pip_get()
    c.goto_xy_safe(source)
    c.move_z(source_height)

    c.set_pump_valve(0, c.PUMP_VALVE_RIGHT) #move valve to right to be able to suck in the fluid
    c.aspirate_ml(0,vol) #suck in the fluid
    c.move_z(300) #move pipette tip out of the vial 
    c.set_pump_valve(0, c.PUMP_VALVE_RIGHT) #move valve to right to be able to move the fluid
    c.aspirate_ml(0,.1) #pull in a another 0.1 mL to avoid drips
    c.set_pump_valve(0, c.PUMP_VALVE_LEFT) #switch valve to left so syringe only sees open air
    c.aspirate_ml(0,.9-vol) # pull syringe down nearly all the way

    c.goto_xy_safe(s_clamp) #go to the clamp
    c.move_z(200) # go the height above the vial
    c.set_pump_valve(0, c.PUMP_VALVE_RIGHT) #set the valve to the right to be able dipsense
    c.dispense_ml(0,1) #push out a fill 1 ml of whatever is in the pipette (liquid and air)
    pip_rem() #remove the pipette tip
    
def purge_pump(pump,n=2,pos=90,vol=None):
    """Function to make sure the lines are full from the source bottles - ready to dispense
    dispenses from a pump, into the waste bucket
    
    if the no volume is given, dispense n time the total syringe volume"""
    if vol==None:
        vol=c.pumps[pump]['volume']*n
    
    ppos=pump_c_pos[pump]+pos #get carousel dispense position for that pump, and offest to the dump location
    c.move_carousel(ppos,17) #move carousel to dump position
    dispense(pump,vol) #dispense into the waste bucket
    c.move_carousel(0,0) #move the carousel home