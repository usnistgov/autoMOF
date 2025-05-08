import pandas as pd
import time

from picotc_read import picotc

from north import NorthC9  # import the class to communicate with the C9 controller
c9 = NorthC9('A',network_serial="AU06D2C0")  # instantiate a C9 controller object with C9 network address A-
t2=NorthC9('B',network=c9.network)



#initialize picotc object
active_channels = [1,2,3,4,5]
pico_thermocouple = picotc(channels = active_channels) #this should automatically run anything in the __init__() method

db=pd.DataFrame()
def temp_entry(active_channels=active_channels):
    ct=time.time()
    heater_temp=t2.get_temp(0) #Get the temperature from North temperature controller
    print(heater_temp)
    #Get the temperatures from the Pico TCs
    #Read thermocouples
    picotc_temp = pico_thermocouple.measure()
    #Unpack readings
    cold_juction = [picotc_temp[0]] # reading of the cold juction
    row={'epoch':ct,'heater':heater_temp, 'pico':cold_juction}
    for ch in active_channels:
        row[f'temp_{ch}']=picotc_temp[ch]
        
    return row


def heater_test(start=30,stop=100,inc=10,dwell=60,meast=30,active_channels=active_channels):
    db=pd.DataFrame(temp_entry(active_channels))
    temps=list(range(start,stop,inc))
    t2.set_temp(0,0)
    t2.enable_channel(0)
    for T in temps:
        t2.set_temp(0,T)
        tstart=time.time()
        while time.time()-tstart<dwell*60:
            row=temp_entry(active_channels)
            row['setpoint']=T
            db=pd.concat([db,pd.DataFrame(row)])
            time.sleep(meast)
            db.to_csv('temps_v2.csv')
    t2.set_temp(0,0)
    t2.disable_channel(0)
        
            
        
    