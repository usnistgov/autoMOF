from north import NorthC9  # import the class to communicate with the C9 controller
from Locator import *  # import the contents of the Locator table (View -> Locator)
c9 = NorthC9('A',network_serial="AU06D2C0")
from convenience import *
import convenience
convenience.c=c9

#def colormix(r,g,b,vial):
vial=5
#c9.goto_safe(rack_left[vial])
#c9.close_gripper()
c9.goto_xy_safe(rack_right[20])
vortex(time=10)