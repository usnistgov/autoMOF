c=None
def sample_pic_test(c):
    for n in range(5):
        c.open_gripper()
        c.goto_safe(rack_left [n])
        c.close_gripper()
        c.goto_safe(camera_pos)
        pic=cam.capture()
        if n==4:
            pic.name=f'room_temp_goop'
        else:
            pic.name=f'Testrun1_vial_{n}'
        pic.save()
        c.goto_safe(rack_left [n])
        c.open_gripper()
    

        