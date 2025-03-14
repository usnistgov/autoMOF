import pandas as pd
import time

from picotc_read import picotc

from north import NorthC9  # import the class to communicate with the C9 controller
c9 = NorthC9('A',network_serial="AU06D2C0")  # instantiate a C9 controller object with C9 network address A-
t2=NorthC9('B',network=c9.network)



#initialize picotc object
active_channels = [1,2,3,4]
pico_thermocouple = picotc(channels = active_channels) #this should automatically run anything in the __init__() method

db=pd.DataFrame()
def temp_entry():
    ct=time.time()
    heater_temp=t2.get_temp(0)
    
    #Read thermocouples
    picotc_temp = pico_thermocouple.measure()
    #Unpack readings
    cold_juction = [picotc_temp[0]] # reading of the cold juction
    temps = [picotc_temp[ch] for ch in active_channels] #list of readings of the active themocouple channels as floats
    
    #TODO add pico tc reading to db
    row={'epoch':ct,'heater':heater_temp, 'pico'}
    return