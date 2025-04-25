# registers and values for the omega7523
# TODO: read/write bit register
# TODO: alarm logic
# TODO: get remaining time/current step num

#register addresses:
PV              = 0x1000   # Measuring unit is 0.1, updated one time in 0.4 second
SV              = 0x1001   # Unit is 0.1, *C or *F
#...
CTRL_METHOD     = 0x1005   # 0: PID, 1: ON/OFF, 2: manual tuning, 3: PID program control
#...
START_PATTERN_N = 0x1030   # 0 ~ 7
ACTUAL_STEP     = [0x1040 + n for n in range(8)]  # 0 ~ 7, indicate that this pattern is executed from step 0 to step N
CYCLE_NUM       = [0x1050 + n for n in range(8)]  # 0 ~ 99 indicate that this pattern has been executed for 1~100 times
LINK_PATTER_NUM = [0x1060 + n for n in range(8)]  # 0 ~ 8, 8 indicates the program end. 0~7 indicates the next pattern
PATTERN_TEMP    = [[0X2000 + 8*i + k for k in range(8)] for i in range(8) ]  # -999 ~ 9,999  PATTERN_TEMP[ptrn_n][step_n]
PATTERN_TIME    = [[0X2080 + 8*i + k for k in range(8)] for i in range(8)]  # 0 ~ 900 (1 minute per scale) PATTERN_TIME[ptrn_n][step_n]



# CTRL_METHOD values:
CTRL_PID        = 0
CTRL_ON_OFF     = 1
CTRL_MANUAL     = 2
CTRL_PROG       = 3

# LINK_PATTERN_NUM values:
PROGRAM_END     = 8


#EXAMPLES
# import omega7523_interface as om
# t8.write_temp_word(3, om.CTRL_METHOD, om.CTRL_PROG)            # enable program control for channel 3
# t8.write_temp_word(3, om.START_PATTERN_N, 2)                   # start pattern number 2
# t8.write_temp_word(3, om.ACTUAL_STEP[2], 4)                    # execute steps 0 to 4 when running pattern 2
# t8.write_temp_word(3, om.LINK_PATTER_NUM[2], om.PROGRAM_END)   # end the program after running pattern 2
# t8.write_temp_word(3, om.PATTERN_TEMP[2][0], 50)               # channel 3 pattern 0 step 0 temp = 50*
# t8.write_temp_word(3, om.PATTERN_TIME[2][0], 30)               # channel 3 pattern 0 step 0 time = 30s
# etc...