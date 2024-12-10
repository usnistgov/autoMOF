from north import NorthC9  # import the class to communicate with the C9 controller
from Locator import *  # import the contents of the Locator table (View -> Locator)
c9 = NorthC9('A',network_serial="AU06D2C0")
from convenience import *
import convenience
convenience.c=c9
c9.default_vel=20
#def colormix(r,g,b,vial):
vial=5
r=2
g=3
b=1
c9.goto_safe(rack_left[vial])
c9.close_gripper()


c9.goto_safe(vclamp)
c9.close_clamp()
c9.uncap()
c9.open_gripper
tare_balance()  #how robust is the balance to gripper forces
c9.close_gripper()
pip_get()
c9.goto_xy_safe(p_rack_right[5])
c9.move_z(120)

c9.set_pump_valve(0, c9.PUMP_VALVE_LEFT)
c9.aspirate_ml(0,.5)
c9.set_pump_valve(0, c9.PUMP_VALVE_RIGHT)


c9.goto_xy_safe(s_clamp)
c9.aspirate_ml(0,.5)
c9.move_z(200)



c9.dispense_ml(0,1)
pip_rem()
c9.open_clamp()
mm=c9.read_steady_scale()

tare_balance()
c9.move_carousel(135,17)
dispense(3,r)
mr=c9.read_steady_scale()

tare_balance()
c9.move_carousel(90,17)


dispense(4,g)
mg=c9.read_steady_scale()

tare_balance()
c9.move_carousel(45,17)
dispense(5,b)
mb=c9.read_steady_scale()

c9.move_carousel(0,0)
c9.goto_xy_safe(clamp)
c9.close_clamp()
c9.move_z(186)
c9.cap(revs=2,torque_thresh=1750)
c9.open_clamp()

c9.goto_safe(camera_pos)
vortex(time=10)
c9.goto_safe(camera_pos)


##add camera caputure

c9.goto_safe(rack_left[vial])
c9.open_gripper()

