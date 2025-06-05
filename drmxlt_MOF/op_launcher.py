
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import time
import threading

from drmxlt_MOF.unit_operation import (Add_fluids, 
                                       Measure_color, 
                                       Preheat_reactor,
                                       Move_to_reactor, 
                                       Start_reaction,
                                       Move_from_reactor, 
                                    #    Move_to_centrifuge,
                                    #    Centrifuge,
                                    #    RM_supernatent,
                                    #    Move_to_sonicator,
                                    #    Sonicate,
                                       )

def op_event(op_name, Sample_ID, c, t, system_db, experiment, event, *args):
    """Launch a particular unit op by name,
    and start an event."""
 
    if op_name == "add_fluids":
        new_sample = True
        if len(args) > 0:
            if "new_sample" in args[0].keys():
                new_sample = args[0]["new_sample"]
        Add_fluids(Sample_ID, c, system_db, experiment, new_sample)
        event.set()

    elif op_name == "measure_color":
        Measure_color(Sample_ID, c, system_db, experiment)
        event.set()

    elif op_name == "preheat_reactor":
        Preheat_reactor(Sample_ID, c, t, system_db, experiment)
        event.set()

    elif op_name == "move_to_reactor":
        Move_to_reactor(Sample_ID, c, system_db, experiment)
        event.set()

    elif op_name == "react":
        end_temp = 10
        if len(args) > 0:
            if "end_temp" in args[0].keys():
                end_temp = args[0]["end_temp"]
        Start_reaction(Sample_ID, c, t, system_db, experiment, end_temp)
        event.set()

    elif op_name == "move_from_reactor":
        Move_from_reactor(Sample_ID, c, system_db, experiment)
        event.set()

    # elif op_name == "move_to_centrifuge":
    #     Move_to_centrifuge(Sample_ID, c, system_db, experiment)
    #     event.set()

    # elif op_name == "centrifuge":
    #     Centrifuge(Sample_ID, c, system_db, experiment)
    #     event.set()
    
    # elif op_name == "rm_supernatent":
    #     RM_supernatent(Sample_ID, c, system_db, experiment)
    #     event.set()

    # elif op_name == "move_to_sonicator":
    #     Move_to_sonicator(Sample_ID, c, system_db, experiment)
    #     event.set()

    # elif op_name == "sonicate":
    #     Sonicate(Sample_ID, c, system_db, experiment)
    #     event.set()

class blocking_event():
    """Dummny class object to conviently re-use op_event function without all the event threading"""

    def set(self):
        return

def execute_scheduled_ops(c, t, system_db, experiment):
   """Function to read in the unit_ops_df
   pull out the names and schedule of each unit op
   and build a scheduler that launches those at the right time"""
   unit_ops_df = experiment.unit_ops_df

   print("Launching Ops") 

   op_start_times = unit_ops_df["Start Time (Ds)"].to_list()
   op_start_times = [time * 10 for time in op_start_times] #convert start times from Ds to s


   op_list = unit_ops_df["UnitOP"].to_list()

   sample_list = unit_ops_df["Sample Name"].to_list()

   event_list = [blocking_event() for i in range(len(op_list))]

   start_time = datetime.now()

   for launch_time, op, sample, event in zip(op_start_times, op_list, sample_list, event_list):
       launch_date = start_time + timedelta(seconds=launch_time)
       

       while True:
            if (datetime.now() > launch_date) | (c.sim == True):
                print(f"Launching {sample} {op} at {launch_time}")
                op_event(op, sample, c, t, system_db, experiment, event)
                print(system_db["left_rack_assignments"][0])
                print(system_db["reactor"][0])
                break
            time.sleep(1)

       


def launch_scheduled_ops(c, t, system_db, experiment):
   
   """Function to read in the unit_ops_df
   pull out the names and schedule of each unit op
   and build a scheduler that launches those at the right time"""
   unit_ops_df = experiment.unit_ops_df


   op_start_times = unit_ops_df["Start Time (Ds)"].to_list()
   op_start_times = [time * 10 for time in op_start_times] #convert start times from Ds to s
   
   op_list = unit_ops_df["UnitOP"].to_list()

   sample_list = unit_ops_df["Sample Name"].to_list()

   event_list = [threading.Event() for i in range(len(op_list))]

   scheduler = BackgroundScheduler()

   start_time = datetime.now()

   for launch_time, op, sample, event in zip(op_start_times, op_list, sample_list, event_list):
       launch_date = start_time + timedelta(seconds=launch_time)
       scheduler.add_job(op_event, 
                         "date", 
                         run_date=launch_date,
                         args=[op, sample, c, t, system_db, experiment, event])
       

   scheduler.start()

   # Wait for all jobs to finish
   for event in event_list:
     event.wait()

   scheduler.shutdown()

