import numpy as np
import MOF_SQL_Tables as mst
import system_db_setup
from sqlmodel import Session, select
from sqlalchemy import func # For getting max and min values from a table
from experiments import Cu_BTC

CAMPAIGN_ID = "Campaign 1"
BATCH_ID = "Batch 1"

def initialize_SQL_tables():
    print("Creating SQL database")
    sqlite_file_name = "SQL Files/MOF_database1.db"
    engine = mst.start_engine(sqlite_file_name)
    mst.create_db_and_tables(engine)
    return engine

def initialize_component_table(engine, num_reactors = 8, positions_per_reactor = 4, positions_in_centrifuge = 6, 
                               positions_in_sonicator = 2):
    with Session(engine) as session:
        # Creating a "Not on platform" dummy component to take locaion [0, 0, 0]
        not_on_platform = mst.Component(name= "Not_On_Platform_Pre_Experiment", loc0= 0, loc1= 0, loc2= 0)
        session.add(not_on_platform)

        # Define vial rack components. 
        # One component will be the vial rack generally for when a task is not assigned to a specific rack.
        general_vial_rack = mst.Component(name= "On_Vial_Rack", loc0= 1, loc1= None, loc2= None)
        session.add(general_vial_rack)
        # Define left vial rack
        for idx in range(48):
            vial_rack_left = mst.Component(name= f"Vial_Rack_Left_{idx}", loc0= 1, loc1= 0, loc2= idx)
            session.add(vial_rack_left)

        # Define right vial rack
        for idx in range(48):
            vial_rack_right = mst.Component(name= f"Vial_Rack_Right_{idx}", loc0= 1, loc1= 1, loc2= idx)
            session.add(vial_rack_right)

        gripper = mst.Component(name= "Gripper", loc0= 2, loc1= 0, loc2= 0)
        session.add(gripper)
        # The Gripper and Clamp should always have the same mutex
        # This is because when the clamp is in use the gripper will be holding a cap and thus be occupied
        clamp = mst.Component(name= "Clamp", loc0= 3, loc1= 0, loc2= 0)
        session.add(clamp)      
            
        for reactor in range(num_reactors):
            new_reactor_key = f"Reactor_{reactor}"
            new_reactor = mst.Component(name= new_reactor_key, loc0= 4, loc1= reactor, loc2= None)
            session.add(new_reactor)
            
            for position in range(positions_per_reactor):
                new_position_key = f"Reactor_{reactor}_{position}"
                new_position = mst.Component(name= new_position_key, loc0= 4, loc1= reactor, loc2= position)
                session.add(new_position)

        centriuge = mst.Component(name= "Centrifuge", loc0= 6, loc1= 0, loc2= None)
        session.add(centriuge)
        for position in range(positions_in_centrifuge):
            new_position_key = f"Centrifuge_{position}"
            new_pos = mst.Component(name= new_position_key, loc0= 6, loc1= 0, loc2= position)
            session.add(new_pos)

        sonicator = mst.Component(name= "Sonicator", loc0= 7, loc1= 0, loc2= None)
        session.add(sonicator)
        for position in range(positions_in_sonicator):
            sonic_position = mst.Component(name= f"Sonicator_{position}", loc0= 7, loc1= 0, loc2= position)
            session.add(sonic_position)

        session.commit()

def initialize_fluids(engine, fluid_db):
    with Session(engine) as session:
        fluid_names = fluid_db.keys()
        for key in fluid_names:
            fluid = fluid_db[key]
            existing_fluid = session.exec(select(mst.FluidConfig).where(
                mst.FluidConfig.name == fluid["Fluid Name"])).first()
            # Check if fluid already exists
            if existing_fluid == None:
                address = fluid["Address"]
                comp_name = f"Syringe_Pump_{address[1]}"
                pump = mst.Component(name= comp_name, loc0= int(address[0]), 
                                     loc1= int(address[1]), loc2= int(address[2])) 


                fluid_config = mst.FluidConfig(key= key, name= fluid["Fluid Name"], formula= "PLACEHOLDER", 
                                        empty_thresh= fluid["Empty threshold"], 
                                        purge_volume= fluid["Purg Vol."], component= pump)
                fluid_event = mst.FluidEventLog(purge_status= fluid["Purged"], 
                                                volume= fluid["Volume (mL)"], fluid= fluid_config)
                session.add(fluid_event)
        session.commit()

def initialize_component_actions(engine):
    with Session(engine) as session:
        components = session.exec(select(mst.Component))
        for c in components:
            component_action = mst.ComponentActionLog(status= None, occupancy= "Empty", 
                                                      mutex= "Available", component= c)
            session.add(component_action)
        session.commit()

def initialize_fluid_events(engine):
    with Session(engine) as session:
        fluid_1 = session.exec(select(mst.FluidConfig).where(mst.FluidConfig.name == "Cu Nitrate")).one()
        fluid_event_1 = mst.FluidEventLog(purge_status= True, volume= 120.0, fluid= fluid_1)
        session.add(fluid_event_1)

        fluid_2 = session.exec(select(mst.FluidConfig).where(mst.FluidConfig.name == "BTC Solution")).one()
        fluid_event_2 = mst.FluidEventLog(purge_status= True, volume= 100.0, fluid= fluid_2)
        session.add(fluid_event_2)

        fluid_3 = session.exec(select(mst.FluidConfig).where(mst.FluidConfig.name == "Water")).one()
        fluid_event_3 = mst.FluidEventLog(purge_status= True, volume= 300.0, fluid= fluid_3)
        session.add(fluid_event_3)

        session.commit()

def initialize_session_history(engine):
    with Session(engine) as session:
        mof_session = mst.SessionHistory(campaign_id= CAMPAIGN_ID, batch_id= BATCH_ID, 
                                         batch_status= "Awaiting Samples", start_time= 0)
        session.add(mof_session)
        session.commit()

def initialize_lab_telemetry(engine):
    with Session(engine) as session:
        #### Poll the lab temperature and humidity ####
        temperature = 0
        humidity = 0
        #########
        telemetry_entry = mst.LabTelemetry(temperature= temperature, humidity= humidity)
        session.add(telemetry_entry)
        session.commit()

def create_new_batch(engine, sample_db):
    with Session(engine) as session:
        session.no_autoflush
        keys = list(sample_db.keys())
        for sample_key in keys:
            sample = sample_db[sample_key]
            #print(sample)
            sample_address = sample["Address"]
            # Need to cast sample_address to int, since its dtype is numpy.int64, not int
            component = session.exec(select(mst.Component).where(mst.Component.loc0 == int(sample_address[0]),
                                                                mst.Component.loc1 == int(sample_address[1]),
                                                                mst.Component.loc2 == int(sample_address[2]))).one()
            sample_info= mst.SampleInfo(sample_id= sample["Sample ID"], barcode= "PLACEHOLDER", 
                                        formula= "PLACEHOLDER",
                                        target_reaction_time= sample["Reaction Time (min)"],
                                        target_reaction_temp= sample["Temperature (C)"],
                                        component_location= component)
            session.add(sample_info)
            location = component.name
            location_log = mst.SampleLocation(location= location, sample= sample_info)
            session.add(location_log)
            print("Sample Name: ", sample["Sample ID"])
            fluid_order = sample["Fluid Order"]
            print("Fluid Order: ", fluid_order)
            idx = 0
            for fluid in fluid_order:
                statement = select(mst.FluidConfig).where(mst.FluidConfig.key == fluid)
                fluid_config = session.exec(statement).one()

                concentration_key = f"Target {fluid} Concentration (mol/L)"
                if concentration_key in sample:
                    target_concentration = sample[concentration_key]
                else:
                    target_concentration = None

                fluid_sample_link = mst.FluidConfigSampleInfoLink(fluid = fluid_config, sample= sample_info, 
                                                    order= idx, target_volume= sample["Experiment Volumes (mL)"][fluid],
                                                    target_concentration= target_concentration)

                session.add(fluid_sample_link)
                idx += 1
        session.commit()

def initialize_sample_locations(engine):
    with Session(engine) as session:
        samples = session.exec(select(mst.SampleInfo))
        for sample in samples:
            location = sample.component_location.name
            location_log = mst.SampleLocation(location= location, sample= sample)
            session.add(location_log)
        session.commit()

def initialize_reactor_use(engine, reactor_df):
    with Session(engine) as session:
        for row_idx in range(len(reactor_df.index)):
            print("ROW IDX: ", row_idx)
            print("reactor_df[Reactor][row idx]: ", reactor_df["Reactor"][row_idx])
            reactor_name = f"Reactor_{reactor_df["Reactor"][row_idx]}"
            reactor_component = session.exec(select(mst.Component).where(mst.Component.name == reactor_name)).one()
            reactor_use = mst.ReactorUse(batch_id= BATCH_ID, 
                                        total_reaction_duration= reactor_df["Total Reactor Duration (Ds)"][row_idx], 
                                        component= reactor_component)
            session.add(reactor_use)
            idx = 0
            for duration, temperature in zip(reactor_df["Reactor Use (Ds)"][row_idx], 
                                             reactor_df["Reactor Temperature (C)"][row_idx]):
                print("Reaction use (Ds): ", reactor_df["Reactor Use (Ds)"][row_idx])
                scheduled_reaction = mst.ReactionInstance(order= idx, reaction_duration= duration, 
                                                            reaction_temperature= temperature, 
                                                            reactor= reactor_use)
                idx += 1
                session.add(scheduled_reaction)
        session.commit()

def initialize_task_schedules(engine, unit_ops_df):
    with Session(engine) as session:
        for row_idx in range(len(unit_ops_df.index)):
            # Get associated sample
            if unit_ops_df["Sample Name"][row_idx] != None:
                sample = session.exec(select(mst.SampleInfo).where(
                    mst.SampleInfo.sample_id == unit_ops_df["Sample Name"][row_idx])).one()
            else:
                sample = None

            # Get associated component
            resource = unit_ops_df["Resource"][row_idx]
            if resource.split()[0] == "Reactor":
                component_name = f"Reactor_{unit_ops_df["Reactor"][row_idx]}"
            elif resource == "Arm&Clamp":
                component_name = "Gripper"
            elif resource == "VialRack":
                component_name = "On_Vial_Rack"
            elif resource == "Centrifuge":
                component_name = "Centrifuge"
            elif resource == "Sonicator":
                component_name = "Sonicator"
            else:
                print("Unable to parse resource name: ", resource)
                component_name = None
            component = session.exec(select(mst.Component).where(mst.Component.name == component_name)).one()

            task_type = unit_ops_df["UnitOP"][row_idx]
            if task_type == "pre_heat_reactor":
                job_type = "Reactor Pre Heating"
            #elif task_type == "centrifuge":
            else:
                job_type = f"Sample Synthesis {sample.sample_id}"

            scheduled_task = mst.TaskSchedule(campaign_id= CAMPAIGN_ID, job_id= "PLACEHOLDER UNIQUE STRING",
                                              job_type= job_type, 
                                              task_id= "PLACEHOLDER UNIQUE STRING", 
                                              task_type= task_type,  
                                              reactor= unit_ops_df["Reactor"][row_idx], 
                                              target_temp= unit_ops_df["Reactor Temperature (C)"][row_idx], 
                                              start_time_Ds= unit_ops_df["Start Time (Ds)"][row_idx], 
                                              end_time_Ds= unit_ops_df["End Time (Ds)"][row_idx], 
                                              sample= sample, component= component)
            session.add(scheduled_task)
        session.commit()

def initialize_task_actions(engine):
    with Session(engine) as session:
        scheduled_tasks = session.exec(select(mst.TaskSchedule))
        for task in scheduled_tasks:
            todo_action = mst.TaskAction(task_status= "To Do", sample= task.sample, 
                                         component= task.component, task_schedule= task)
            session.add(todo_action)
        session.commit()

def initialize_reactor_telemetry(engine):
    with Session(engine) as session:
        #### Poll the reactor temperatures ####
        reactor_blocks = session.exec(select(mst.Component).where(
            mst.Component.loc0 == 4, mst.Component.loc2 == None))
        for block in reactor_blocks:
            telemetry = mst.ReactorTelemetry(temperature= 0, reactor= block)
            session.add(telemetry)
        #########
        session.commit()

def append_component_action(engine, status, occupancy, mutex, comp_address, task_id):
    with Session(engine) as session:
        component = session.exec(select(mst.Component).where(mst.Component.loc0 == comp_address[0], 
                                                             mst.Component.loc1 == comp_address[1], 
                                                             mst.Component.loc2 == comp_address[2])).one()
        task_schedule = session.exec(select(mst.TaskSchedule).where(mst.TaskSchedule.id == task_id)).one()
        component_action = mst.ComponentActionLog(status= status, occupancy= occupancy, mutex= mutex, 
                                                  component= component, task_schedule= task_schedule)
        session.add(component_action)
        session.commit()

def append_fluid_event(engine, purge_status, volume, fluid_key):
    with Session(engine) as session:
        fluid = session.exec(select(mst.FluidConfig).where(mst.FluidConfig.key == fluid_key)).one()
        fluid_event = mst.FluidEventLog(purge_status= purge_status, volume= volume, fluid= fluid)
        session.add(fluid_event)
        session.commit()

def update_session_end(engine, campaign_id, batch_id, batch_status, end_time, end_report):
    with Session(engine) as session:
        mof_session = session.exec(select(mst.SessionHistory).where(
            mst.SessionHistory.campaign_id == campaign_id, 
            mst.SessionHistory.batch_id == batch_id))
        mof_session.batch_status = batch_status
        mof_session.end_time = end_time
        mof_session.end_report = end_report
        session.add(mof_session)
        session.commit()

def append_sample_location(engine, location, sample_id, task_id):
    with Session(engine) as session:
        sample = session.exec(select(mst.SampleInfo).where(mst.SampleInfo.sample_id == sample_id))
        task = session.exec(select(mst.TaskSchedule).where(mst.TaskSchedule.id == task_id))
        sample_location = mst.SampleLocation(location= location, sample= sample, task_schedule= task)
        session.add(sample_location)
        session.commit()



def main():
    # Cu_BTC Experiment
    print("Initializing local databases")
    experiment = Cu_BTC()
    engine = initialize_SQL_tables()
    initialize_component_table(engine)
    initialize_fluids(engine, experiment.fluid_db)
    initialize_component_actions(engine)
    #initialize_fluid_events(engine)
    initialize_session_history(engine)
    initialize_lab_telemetry(engine)
    create_new_batch(engine, experiment.sample_db)
    #initialize_sample_locations(engine)

if __name__ == "__main__":
    main()
    