import numpy as np
from north import NorthC9  # import the class to communicate with the C9 controller
from Locator import *  # import the contents of the Locator table (View -> Locator)
c9 = NorthC9('A',network_serial="AU06D2C0")
from convenience import *
import convenience
convenience.c=c9
c9.default_vel=20
from time import sleep


from north_simple_camera import SimpleCamera, SimplePhoto
import im_proc
cam = SimpleCamera(1)

if c9.sim:
    sleep(2)
    
    
def colormix(vial,comp):
    # vial=5
    # r=2
    # g=3
    # b=1
    #return(comp,np.array([1,2,3],dtype='float32'))
    c9.move_carousel(0,0)
    r, g, b = list(comp)
    c9.goto_safe(rack_left[vial])
    c9.close_gripper()


    c9.goto_safe(vclamp)
    c9.close_clamp()
    c9.uncap()
    c9.move_z(300)
    c9.open_clamp()
    #c9.open_gripper()
    tare_balance()  #how robust is the balance to gripper forces
    #c9.close_gripper()
    if vial<12:
        pipette()
    else:
        pipette(source=p_rack_right[4])
    #c9.open_clamp()
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
    c9.goto(camera_pos)

    pic = cam.capture()
    c9.delay(5)
    #print(pic.get_size())
    cropped, original = im_proc.crop_img(pic.img, *[590, 350, 660, 450])
    avg_color = im_proc.get_color(cropped)
    #SimplePhoto(original).show()
    #avg_color_tile = SimplePhoto(np.tile(avg_color, reps=(200, 200, 1)))
    #avg_color_tile.show()
    print(avg_color)

    c9.goto_safe(rack_left[vial])
    c9.open_gripper()
    mcolor= np.flipud(avg_color)#flip to swith from bgr to rgb space
    mass=np.array([mr,mg,mb],dtype='float32')
    return(mcolor,mass,pic)

