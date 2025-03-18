import sys
import os

sys.path.append(os.getcwd() + '/..')

from north import NorthC9  # import the class to communicate with the C9 controller


from drmxlt_MOF.system_db_setup import system_db
from sample_db_setup import sample_db
from fluid_trakcing import fluid_db

from drmxlt_MOF.unit_operation import Add_fluids
from drmxlt_MOF.moving_vials import Move_Sample
from drmxlt_MOF.votex import vortex
from drmxlt_MOF.im_proc import get_ave_color
from drmxlt_MOF.north_simple_camera import SimpleCamera


c9 = NorthC9('A',network_serial="AU06D2C0") #Initialize the robot controller
cam = SimpleCamera() #Initialize the camera


#Walk through the existing samples and execute those experiments
list_of_samples = []
for key in sample_db.keys():
    list_of_samples.append(sample_db[key]["Sample ID"])


for sample in list_of_samples:
    #add the fluids to the vial
    Add_fluids(sample, c9, system_db, sample_db, fluid_db, new_sample=True)

    #Mix the fluids in the vial
    vortex(c9)


    #take a picture and get the color
    pic = cam.capture()
    color = get_ave_color(pic)

    #Move sample back to an available spot in the rack
    new_address = find_open_vial_rack_position(system_db)
    Move_Sample(sample, new_address, sample_db, system_db, c9)

    








