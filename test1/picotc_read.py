
import ctypes
import numpy as np
from picosdk.usbtc08 import usbtc08 as tc08
from picosdk.functions import assert_pico2000_ok


class picotc():

    def __init__(self, channels = [1], types = None):
        """
        channels is a list of channels (other than the cold junction on channel 0) that are active
        types is a list that should be the same length as channels for the type of thermocouple
            type = 75 --> K
        """
        # Create chandle and status ready for use
        self.chandle = ctypes.c_int16()
        self.status = {}

        # open unit
        self.status["open_unit"] = tc08.usb_tc08_open_unit()
        assert_pico2000_ok(self.status["open_unit"])
        self.chandle = self.status["open_unit"]

        # set mains rejection to 50 Hz
        self.status["set_mains"] = tc08.usb_tc08_set_mains(self.chandle,0)
        assert_pico2000_ok(self.status["set_mains"])
        
        
        if types == None:
            types = [75 for ch in channels]
            
            
        for ch, tctype in zip(channels,types):

            # set up channel
            # therocouples types and int8 equivalent
            # B=66 , E=69 , J=74 , K=75 , N=78 , R=82 , S=83 , T=84 , ' '=32 , X=88 
            typeK = ctypes.c_int8(tctype)
            self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, ch, typeK)
            assert_pico2000_ok(self.status["set_channel"])

            # get minimum sampling interval in ms
            self.status["get_minimum_interval_ms"] = tc08.usb_tc08_get_minimum_interval_ms(self.chandle)
            assert_pico2000_ok(self.status["get_minimum_interval_ms"])
        
    def measure(self):    

        # get single temperature reading
        temp = (ctypes.c_float * 9)()
        overflow = ctypes.c_int16(0)
        units = tc08.USBTC08_UNITS["USBTC08_UNITS_CENTIGRADE"]
        self.status["get_single"] = tc08.usb_tc08_get_single(self.chandle,ctypes.byref(temp), ctypes.byref(overflow), units)
        assert_pico2000_ok(self.status["get_single"])
        
        return temp

    def close_unit():
        # close unit
        self.status["close_unit"] = tc08.usb_tc08_close_unit(self.chandle)
        assert_pico2000_ok(self.status["close_unit"])
