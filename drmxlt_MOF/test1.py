from north import NorthC9  # import the class to communicate with the C9 controller
from Locator import *  # import the contents of the Locator table (View -> Locator)
c9 = NorthC9('A',network_serial="AU06D2C0")  # instantiate a C9 controller object with C9 network address A-

#dispense the full volume of a syringe pump

def max_dispense(pump_num):

    dispense(pump_num, c9.pumps[pump_num]['volume'])
 
#general dispense function

#will dispense 10mL with 2 strokes given 5mL syringe

def dispense(pump_num, ml_remaining):

    while ml_remaining > c9.pumps[pump_num]['volume']:

        max_dispense(pump_num)

        c9.delay(0.2)

        ml_remaining -= c9.pumps[pump_num]['volume']

    c9.set_pump_valve(pump_num, c9.PUMP_VALVE_LEFT)

    c9.aspirate_ml(pump_num, ml_remaining)

    c9.delay(0.2)

    c9.set_pump_valve(pump_num, c9.PUMP_VALVE_RIGHT)

    c9.dispense_ml(pump_num, ml_remaining)
 



 
c9.default_vel=20
#c9.home_robot()
#c9.home_carousel()
#c9.move_carousel(0,0)
#c9.home_pump(5)


c9.goto_safe(rack_left[0])
c9.close_gripper()
c9.goto_xy_safe(clamp)
c9.move_z(181)#go to 11100
c9.close_clamp()
c9.uncap() #2mm/rev and 2 revs to remove cap  Uncapped at 10600=186
c9.goto_safe(home)

c9.move_carousel(45,17)
c9.open_clamp()
c9.zero_scale()
while c9.read_steady_scale() != 0:
    c9.zero_scale()
dispense(5,8)
c9.move_carousel(0,0)
c9.goto_xy_safe(clamp)
c9.close_clamp()
c9.move_z(186)
c9.cap(revs=2,torque_thresh=1750)
c9.open_clamp()
c9.goto_safe(rack_left[0])
c9.open_gripper()
c9.goto_safe(home)

