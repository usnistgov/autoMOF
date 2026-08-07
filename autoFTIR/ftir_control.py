#import serial
import time
import os
import subprocess
import signal
import li850 as gas
import spa_converter as conv
from spa_converter import SPAConverter as spa
from alicat_driver import AlicatController 
from valve_switcher import ModularUniversalActuator 
from auto_clicker import AutoClicker
from server_csv import start_server, stop_server
from vacuumPy import SolenoidController


valve = ModularUniversalActuator(port = 'COM6')
mfc = AlicatController (port = 'COM5')
ard = SolenoidController(port = 'COM8')
auto = AutoClicker()


def mfc_test():
    mfc.set_flow('co2', 50)
    mfc.set_flow('n2', 50)
    print(mfc.get_flow('co2'))
    print(mfc.get_flow('n2'))
    time.sleep(10)
    mfc.set_flow('co2', 0)
    mfc.set_flow('n2', 0)
    print(mfc.get_flow('co2'))
    print(mfc.get_flow('n2'))
    
def valve_test_b():
    valve.move_to_b()

def valve_test_a():
    valve.move_to_a()

# Clicker Test:
def clicker_test():
    auto.setup_coordinates()
    conv.start_workflow(auto)
    print("Workflow active. Waiting for CSVs to trigger measurements...")
    auto.click_bg()
    
    

# Test for programatic workflow. Autoclicks and handles data conversion.
def convert_test(n=3, s=3):
    auto.setup_omnic()
    auto.setup_autopro()
    conv_handler, observer = conv.start_workflow(auto)
 
    i = 1
    while n > 0:
        auto.click_expt_set()
        time.sleep(3)
        auto.click_after_mins()
        time.sleep(3)
        auto.click_ok()
        time.sleep(3)
        
        conv_handler.current_scan = i
        print(f"--- Step {i} ---") 
        auto.click_bg()
        auto.click_bg()
        while conv_handler.last_csv_created is None:
            time.sleep(1)
        conv_handler.last_csv_created = None
        auto.click_meas()
        auto.click_meas()
        for j in range(s):
            print(f"Scanning well {j+1} of {s}")
            while conv_handler.last_csv_created is None:
                time.sleep(5)
            conv_handler.last_csv_created = None
        #files_converted = 0
        #while files_converted < s:
           # if conv_handler.last_csv_created is not None:
                #files_converted += 1
                #print(f"Measurement CSV {files_converted} of {s} detected!")
                #conv_handler.last_csv_created = None
            #else:
                #time.sleep(1)
        i += 1
        n -= 1

def setup():
    auto.setup_omnic()
    auto.setup_autopro()
    gas.config()
    conv.start_workflow()



def co2_step(t0=10, n=3, s=4, tf= 100, cf0=1, pret=600, pref=100, h=10, m=5): #step function
    """ 
    FTIR CONTROL FUNCTION: 
    This is the main control function for the FTIR process. 
    The main loop waits t0 seconds
    clears the background
    takes a background measurement
    takes a measurement for each of the s active wells
    once all measuremnts are taken for a step, step up flow of co2
    repeat until all steps are taken

    Parameters
    ----------

    t0: int
     time per step
    n: int
     number of steps
    s: int
     number of active wells (including background)
    tf: int
     total flow (co2 + n2)
    cf0: int
     initial flow co2
    pret: int
     time for n2 to flush system
    h: int
     step size
    m: int
     # of measurements per step

    """
    #Clicker Setup
    auto.setup_omnic()
    auto.setup_autopro()
    # File detector starts observing
    conv_handler, observer = conv.start_workflow(auto)
    #Start gas data collection
    start_server()
    #Gas setup
    
    valve.move_to_a() #mks (pure_n2) in
    time.sleep(2)
    mfc.set_flow('n2', tf-cf0) 
    mfc.set_flow('co2', cf0) 
    print(mfc.get_flow('n2'))
    print(mfc.get_flow('co2'))
    mfc.set_flow('pure_n2', pref)
    print(mfc.get_flow('pure_n2'))
    time.sleep(pret) 
    valve.move_to_b() # alicat (CO2 and N2 mix)

    i = 1
    while n > 0:
        print(f"--- Step {i} ---")
        while m > 0:
            print(f"{m} Measurements left for Step {i}")
            #Reset Background
            time.sleep(t0) 
            auto.click_expt_set()
            time.sleep(3)
            auto.click_after_mins()
            time.sleep(3)
            auto.click_ok()
            time.sleep(3)
            # Take Background and wait for file to save
            auto.click_bg()
            while conv_handler.last_csv_created is None:
                time.sleep(1)
            conv_handler.last_csv_created = None
            # Take Measurement and wait for file to save
            # Twice because sometimes it needs a double click to register
            auto.click_meas()
            auto.click_meas()
            files_converted = 0
            while files_converted < s:
                if conv_handler.last_csv_created is not None:
                    files_converted += 1
                    print(f"Measurement CSV {files_converted} of {s} detected!")
                    conv_handler.last_csv_created = None
                else:
                    time.sleep(1)
            m -=1

        cf0 += h
        mfc.set_flow('n2', tf-cf0)
        mfc.set_flow('co2', cf0)
        print(mfc.get_flow('n2'))
        print(mfc.get_flow('co2'))
        i += 1
        n -= 1

    else:
        valve.move_to_a()
        stop_server()
        mfc.set_flow('co2', 0)
        mfc.set_flow('n2', 0)
        mfc.set_flow('pure_n2', 0)



def co2_bar(t0=10, n=3, tf=100, cf0=1, pret=600, h=10, st=10):
    """
    CO2 Bar Function:

    Set flow A
    check concentration
    wait t0
    set flow 0
    measure final concentration
    start flow at next concentration (+h)

    Parameters
    ----------
    t0: int
        time per step
    n: int
        number of steps 
    tf: int
        total flow (co2 + n2)
    cf0: int
        initial flow co2
    pret: int
        time for n2 to flush system
    h: int
        step size
    st: int
        wait time after setting CO2 flow to zero but before taking measurement

    """
    auto.setup_omnic()
    auto.setup_autopro()
        # File detector starts observing
    conv_handler, observer = conv.start_workflow(auto)
        #Start gas data collection
    start_server()
    
    valve.move_to_a()
    time.sleep(2)
    mfc.set_flow('n2', tf-cf0) 
    mfc.set_flow('co2', cf0)
    print(mfc.get_flow('n2'))
    print(mfc.get_flow('co2'))
    time.sleep(pret)
    valve.move_to_b()

    while n > 0:
        
        print(f"--- Step {i} ---")
        time.sleep(t0)
        mfc.set_flow('co2', 0)
        mfc.set_flow('n2', tf)
        print(mfc.get_flow('co2'))
        print(mfc.get_flow('n2'))
        time.sleep(st)
        
        #autoclicker
        auto.click_expt_set()
        time.sleep(3)
        auto.click_after_mins()
        time.sleep(3)
        auto.click_ok()
        time.sleep(3)
        # Take Background and wait for file to save
        auto.click_bg()
        while conv_handler.last_csv_created is None:
            time.sleep(1)
        conv_handler.last_csv_created = None
        # Take Measurement and wait for file to save
        # Twice because sometimes it needs a double click to register
        auto.click_meas()
        auto.click_meas()
        files_converted = 0
        while files_converted < s:
            if conv_handler.last_csv_created is not None:
                files_converted += 1
                print(f"Measurement CSV {files_converted} of {s} detected!")
                conv_handler.last_csv_created = None
            else:
                time.sleep(1)
        cf0 += h
        mfc.set_flow('n2', tf-cf0)
        mfc.set_flow('co2', cf0)
        print(mfc.get_flow('n2'))
        print(mfc.get_flow('co2'))
        i+= 1
        n -=1

    else:
        valve.move_to_a()
        stop_server()
        mfc.set_flow('co2', 0)
        mfc.set_flow('n2', 0)
        mfc.set_flow('pure_n2', 0)

