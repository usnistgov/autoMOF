# t8 ramp soak test
from north import NorthC9
import omega7523_interface as om


c9 = NorthC9('A', network_serial="FT6VE3MC", heartbeat=True)
t8 = NorthC9('B', network = c9.network, heartbeat=True)

# t8.write_temp_word(0, om.CTRL_METHOD, om.CTRL_PROG)            # enable program control for channel 3
# t8.write_temp_word(0, om.START_PATTERN_N, 2)                   # start pattern number 2
# t8.write_temp_word(0, om.CYCLE_NUM[2], 0)                      # execute pattern 2 cycle num + 1 times
# t8.write_temp_word(0, om.ACTUAL_STEP[2], 5)                    # execute steps 0 to 4 when running pattern 2
# t8.write_temp_word(0, om.LINK_PATTER_NUM[2], om.PROGRAM_END)   # end the program after running pattern 2
# 
# t8.write_temp_word(0, om.PATTERN_TEMP[2][0], 700)               # channel 3 pattern 0 step 0 temp = 50*
# t8.write_temp_word(0, om.PATTERN_TIME[2][0], 3)                # channel 3 pattern 0 step 0 time = 30s
# 
# t8.write_temp_word(0, om.PATTERN_TEMP[2][1], 700)              
# t8.write_temp_word(0, om.PATTERN_TIME[2][1], 2)
# 
# t8.write_temp_word(0, om.PATTERN_TEMP[2][2], 900)              
# t8.write_temp_word(0, om.PATTERN_TIME[2][2], 3)
# 
# t8.write_temp_word(0, om.PATTERN_TEMP[2][3], 900)              
# t8.write_temp_word(0, om.PATTERN_TIME[2][3], 2)
# 
# t8.write_temp_word(0, om.PATTERN_TEMP[2][4], 700)              
# t8.write_temp_word(0, om.PATTERN_TIME[2][4], 3)
# 
# t8.write_temp_word(0, om.PATTERN_TEMP[2][5], 700)              
# t8.write_temp_word(0, om.PATTERN_TIME[2][5], 2)


