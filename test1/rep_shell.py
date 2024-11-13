from north import NorthC9  # import the class to communicate with the C9 controller
from Locator import *  # import the contents of the Locator table (View -> Locator)
#c9 = NorthC9('A',network_serial="AU06D2C0",proj_path=r"C:\\Users\\hjoress\\OneDrive - NIST\\Documents 1\\robot_setup\\test1")  # instantiate a C9 controller object with C9 network address A-
c9 = NorthC9('A',network_serial="AU06D2C0")  # instantiate a C9 controller object with C9 network address A-

from convenience import *
import convenience
convenience.c=c9

from north_simple_camera import SimpleCamera, SimplePhoto
import im_proc

cam = SimpleCamera(1)