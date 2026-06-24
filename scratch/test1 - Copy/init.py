from north import NorthC9  # import the class to communicate with the C9 controller
from Locator import *  # import the contents of the Locator table (View -> Locator)
c9 = NorthC9('A',network_serial="AU06D2C0")  # instantiate a C9 controller object with C9 network address A-
from convenience import *
c=c9


 
c9.default_vel=5
print('homing robot')
c9.home_robot()
print("robot homing complete; homing carousel")
c9.home_carousel()
c9.move_carousel(0,0)
print('carousel homed; homing pumps')
#c9.home_pump(5)

