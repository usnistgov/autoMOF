import numpy as np

from north import NorthC9
import drmxlt_MOF.omega7523_interface as om


# c9 = NorthC9('A', network_serial="FT6VE3MC", heartbeat=True)
# t8 = NorthC9('B', network = c9.network, heartbeat=True)



def temp_ramp_up_hold_down(t8, channel: int, target_temp: float, dwell_time: int, end_temp: float=20,
              ramp_up_rate:float =10, ramp_down_rate: float=10, pattern_num: int=0):
    """
    Ramps up to a target temp of the given channel at the given rate, holds for dwell time (int, minutes), then ramps
    up or down (note: not actively cooled, if the requested ramp down rate is too steep it will not be accurately
    followed) to the end_temp. Finally, returns the channel to PID control mode.
    Pattern num chooses which "pattern" to program on the device, there are 8, can be safely left at 0 if you haven't
    manually programmed something in another pattern (this would overwrite your manual program).
    
    """
    t8.disable_channel(channel)
    t8.write_temp_word(channel, om.CTRL_METHOD, om.CTRL_PROG)            # enable program control for channel 3
    t8.write_temp_word(channel, om.START_PATTERN_N, pattern_num)         # start at pattern number 0
    t8.write_temp_word(channel, om.CYCLE_NUM[pattern_num], 0)            # execute pattern 0 cycle num + 1 times, ie. just do it once
    t8.write_temp_word(channel, om.ACTUAL_STEP[pattern_num], 2)          # execute steps 0 to 4 when running pattern 0
    t8.write_temp_word(channel, om.LINK_PATTER_NUM[pattern_num], om.PROGRAM_END)   # end the program after running pattern 0

    starting_temp = t8.get_temp(channel)
    temp_diff_up = abs(target_temp - starting_temp)
    ramp_up_time = int(temp_diff_up/ramp_up_rate)+1  # note: rounds up time in minutes, rate is slightly slower

    temp_diff_down = abs(end_temp - target_temp)
    ramp_down_time = int(temp_diff_down/ramp_down_rate)+1  # note: rounds up time in minutes, rate is slightly slower

    t8.write_temp_word(channel, om.PATTERN_TEMP[pattern_num][0], target_temp)  # channel pattern num step 0 temp = target_temp
    t8.write_temp_word(channel, om.PATTERN_TIME[pattern_num][0], ramp_up_time)    # channel pattern num step 0 time = ramp_time

    t8.write_temp_word(channel, om.PATTERN_TEMP[pattern_num][1], target_temp)  # channel pattern num step 0 temp = target_temp
    t8.write_temp_word(channel, om.PATTERN_TIME[pattern_num][1], int(dwell_time))    # channel pattern num step 0 time = ramp_time

    t8.write_temp_word(channel, om.PATTERN_TEMP[pattern_num][2], end_temp)  # channel pattern num step 0 temp = target_temp
    t8.write_temp_word(channel, om.PATTERN_TIME[pattern_num][2], ramp_down_time)    # channel pattern num step 0 time = ramp_time
    
    t8.enable_channel(channel)  # start the routine
    
    #t8.delay( (ramp_up_time + dwell time + ramp_down_time)*60 )   # this will block your program for the length of the ramps
    #t8.write_temp_word(channel, om.CTRL_METHOD, om.CTRL_PID)            # enable program control for channel 3
    
def hold_temp(t8, channel, temp):
    # will hold the given temp indefinitely
    print(f"hold_temp channel = {channel}")
    set_PID_mode(t8, channel)
    t8.set_temp(temp)
    t8.enable_channel(channel)
        
def set_PID_mode(t8, channel):
    print(f"set_PID_mode channel = {channel}")
    t8.write_temp_word(channel, om.CTRL_METHOD, om.CTRL_PID) 


def read_temperature(t8, channel):
    temperature = t8.get_temp(channel)
    return temperature

def Reactor_ready_check(t8, channel, target_temperature, tolerance = 5):
    current_temperature = t8.get_temp(channel)

    offset = np.abs(target_temperature - current_temperature)

    if offset < tolerance:
        ready = True

    else:
        ready = False

    return ready