


# from drmxlt_MOF.Locator import *
from Locator import *


def vortex(c, time=30,vel=50,amp=1000):
    """Function to shake the vial in the gripper to mix any fluids"""

    #Near the camera position is a safe place to shake the vials
    c.goto_safe(camera_pos)

    dis=vel*1000*time
    print(dis)
    vt=c.move_axis(0,dis,vel=vel,wait=0)
    elbow_pos = c.get_axis_position(1)
    while not vt.is_done():
        c.move_axis(1, elbow_pos+amp,vel=30,accel=30)
        c.move_axis(1, elbow_pos-amp,vel=30,accel=30)
    c.reduce_axis_position(0)

    #Make sure that vial ends up a the location we started
    c.goto_safe(camera_pos)