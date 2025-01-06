from north import NorthC9  # import the class to communicate with the C9 controller
from Locator import *  # import the contents of the Locator table (View -> Locator)
from system_state_tools import find_vial, find_liquid, check_stock_solution
c9 = NorthC9('A',network_serial="AU06D2C0")  # instantiate a C9 controller object with C9 network address A-

c9.goto_safe(rack_left[0])