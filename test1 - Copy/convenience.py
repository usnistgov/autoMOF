c=None
from Locator import *

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

    c.set_pump_valve(pump_num, c.PUMP_VALVE_LEFT)

    c.aspirate_ml(pump_num, ml_remaining)

    c.delay(0.2)

    c.set_pump_valve(pump_num, c.PUMP_VALVE_RIGHT)

    c.dispense_ml(pump_num, ml_remaining)
 
def tare_balance():
    c.zero_scale()
    while c.read_steady_scale() != 0:
        c.delay(.2)
        c.zero_scale()
        
        

    
pipette_order = [i for i in range(2, 48, 3)] \
                + [i for i in range(1, 48, 3)] \
                + [i for i in range(0, 48, 3)]

next_pip_i = -1
def next_pipette():
    global next_pip_i
    next_pip_i += 1
    return pipette_order[next_pip_i]
 
#c9.goto_safe(p_up[next_pipette])

def pip_get(ind=None):
    if ind is None:
        ind = next_pipette()
    c.goto_safe(p_up[ind])
    c.goto_safe(p_up_wp)
    
def pip_rem():
    c.goto_safe(p_remover_ap)
    c.goto(p_rem,vel=5,accel=5)
    c.move_z(292)
    
def vortex(time=30,vel=50,amp=1000):
    dis=vel*1000*time
    print(dis)
    vt=c.move_axis(0,dis,vel=vel,wait=0)
    elbow_pos = c.get_axis_position(1)
    while not vt.is_done():
        c.move_axis(1, elbow_pos+amp,vel=80)
        c.move_axis(1, elbow_pos-amp,vel=80)
    c.reduce_axis_position(0)
