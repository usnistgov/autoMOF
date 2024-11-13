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
    sleep(2) #the simulator need a 2 s to initialize the camera
    
    
def colormix(vial,comp):
    # vial=5
    # r=2
    # g=3
    # b=1
    #return(comp,np.array([1,2,3],dtype='float32'))
    c9.move_carousel(0,0) # move carousel to home (out of the way)
    r, g, b = list(comp) # un-pack the components

    #Pick up the vial
    c9.goto_safe(rack_left[vial])
    c9.close_gripper()

    #Take the vial to the clamp and un-cap
    c9.goto_safe(vclamp)
    c9.close_clamp()
    c9.uncap()
    c9.move_z(300)

    # Pipette from source vial
    c9.open_clamp() # to allow a good tare 
    #c9.open_gripper()
    tare_balance()  
    #c9.close_gripper()
    if vial<12: #only about 12 dispenses worth of fluid in one source vial
        pipette()
    else:
        pipette(source=p_rack_right[4])
    #c9.open_clamp()
    mm=c9.read_steady_scale() #measure the mass that was dispensed


    #Dispensing from pumps
    tare_balance()
    c9.move_carousel(135,17) #135 is the position for pump 3
    dispense(3,r) #dispense from pump 3
    mr=c9.read_steady_scale()

    tare_balance()
    c9.move_carousel(90,17) #90 is the position for pump 4
    dispense(4,g) #dispense from pump 4
    mg=c9.read_steady_scale()

    tare_balance()
    c9.move_carousel(45,17) #45 is position for pump 5
    dispense(5,b) #dispense from pump 3
    mb=c9.read_steady_scale()


    #moves carousel out the way and caps the vial, and gets ready to move vial
    c9.move_carousel(0,0)
    c9.goto_xy_safe(clamp)
    c9.close_clamp()
    c9.move_z(186)
    c9.cap(revs=2,torque_thresh=1750)
    c9.open_clamp()

    #move vial in front of camera, stir a bit
    c9.goto_safe(camera_pos)
    vortex(time=10)
    c9.goto(camera_pos)

    # Take a picture, and report average color
    pic = cam.capture()
    c9.delay(5)
    #print(pic.get_size())
    cropped, original = im_proc.crop_img(pic.img, *[590, 350, 660, 450])
    avg_color = im_proc.get_color(cropped)
    #SimplePhoto(original).show()
    #avg_color_tile = SimplePhoto(np.tile(avg_color, reps=(200, 200, 1)))
    #avg_color_tile.show()
    print(avg_color)

    # Return the vial to the rack
    c9.goto_safe(rack_left[vial])
    c9.open_gripper()

    # output the measurements of color, mass, and the picture
    mcolor= np.flipud(avg_color)#flip to swith from bgr to rgb space
    mass=np.array([mr,mg,mb],dtype='float32')
    return(mcolor,mass,pic)

