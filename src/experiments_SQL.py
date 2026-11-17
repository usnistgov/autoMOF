import numpy as np
import pandas as pd
import src.sql_tables as mst
import src.system_db_setup
from sqlmodel import Session, select
from sqlalchemy import func # For getting max and min values from a table
from src.experiments import Cu_BTC

CAMPAIGN_ID = "Campaign 1"
# BATCH_ID = "Batch 1"

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

        pipettes = mst.Component(name= "Pipette_Rack", loc0= 8, loc1= 0, loc2= None)
        session.add(pipettes)
        for idx in range(48):
            pipette = mst.Component(name= f"Pipette_{idx}", loc0= 8, loc1= 1, loc2= idx)
            session.add(pipette)

        needles = mst.Component(name= "Needle_Rack", loc0= 9, loc1= 0, loc2= None)
        session.add(needles)
        for idx in range(48):
            needle = mst.Component(name= f"Needle_{idx}", loc0= 9, loc1= 1, loc2= idx)
            session.add(needle)  

        session.commit()

def initialize_fluids(engine, fluid_db, batch_id):
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
                if "Concentration (mol/L)" in fluid:
                    concentration = fluid["Concentration (mol/L)"]
                else:
                    concentration = None
                fluid_config = mst.FluidConfig(key= key, name= fluid["Fluid Name"],
                                               batch_id= batch_id,  
                                               formula= "PLACEHOLDER", 
                                               empty_thresh= fluid["Empty threshold"], 
                                               purge_volume= fluid["Purg Vol."], 
                                               concentration=  concentration, component= pump)
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

def initialize_session_history(engine, batch_id):
    with Session(engine) as session:
        mof_session = mst.SessionHistory(campaign_id= CAMPAIGN_ID, batch_id= batch_id, 
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

def create_new_batch(engine, sample_db, batch_id):
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
                                        formula= "PLACEHOLDER", batch_id= batch_id, 
                                        target_reaction_time= sample["Reaction Time (min)"],
                                        target_reaction_temp= sample["Temperature (C)"],
                                        component_location= component)
            session.add(sample_info)
            location = component.name
            location_log = mst.SampleLocation(sample= sample_info, component_location= component)
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
            location = sample.component_location
            location_log = mst.SampleLocation(sample= sample, component_location= location)
            session.add(location_log)
        session.commit()

def initialize_reactor_use(engine, reactor_df, batch_id):
    with Session(engine) as session:
        for row_idx in range(len(reactor_df.index)):
            print("ROW IDX: ", row_idx)
            print("reactor_df[Reactor][row idx]: ", reactor_df["Reactor"][row_idx])
            reactor_name = f"Reactor_{reactor_df["Reactor"][row_idx]}"
            reactor_component = session.exec(select(mst.Component).where(mst.Component.name == reactor_name)).one()
            reactor_use = mst.ReactorUse(batch_id= batch_id, 
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
                Exception("Unable to parse resource name: ", resource)
                component_name = None
            component = session.exec(select(mst.Component).where(mst.Component.name == component_name)).one()

            task_type = unit_ops_df["UnitOP"][row_idx]
            if task_type == "pre_heat_reactor":
                job_type = "Reactor Pre Heating"
            #elif task_type == "centrifuge":
            elif sample != None:
                job_type = f"Sample Synthesis {sample.sample_id}"
            else:
                Exception("Sample is None for non pre heating task.")

            scheduled_task = mst.TaskSchedule(campaign_id= CAMPAIGN_ID, job_id= "PLACEHOLDER UNIQUE STRING",
                                              job_type= job_type, 
                                              batch_id= unit_ops_df["Batch Number"][row_idx], 
                                              task_id= "PLACEHOLDER UNIQUE STRING", 
                                              duration= unit_ops_df["Duration (Ds)"][row_idx], 
                                              task_type= task_type,  
                                              reactor= unit_ops_df["Reactor"][row_idx], 
                                              target_temp= unit_ops_df["Reactor Temperature (C)"][row_idx], 
                                              start_time_Ds= unit_ops_df["Start Time (Ds)"][row_idx], 
                                              end_time_Ds= unit_ops_df["End Time (Ds)"][row_idx], 
                                              step= int(unit_ops_df["Step"][row_idx]), 
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
            telemetry = mst.ReactorTelemetry(temperature= None, reactor= block)
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

def append_sample_location(engine, component_name, sample_id, task_id):
    with Session(engine) as session:
        sample = session.exec(select(mst.SampleInfo).where(mst.SampleInfo.sample_id == sample_id)).one()
        task = session.exec(select(mst.TaskSchedule).where(mst.TaskSchedule.task_id == task_id)).one()
        component = session.exec(select(mst.Component).where(mst.Component.name == component_name)).one()
        sample_location = mst.SampleLocation(sample= sample, task_schedule= task, component_location= component)
        session.add(sample_location)
        session.commit()

def check_out_pipette(engine, pipette_index, task_id):
    with Session(engine) as session:
        pipette = session.exec(select(mst.Component).where(mst.Component.loc0 == 8, 
                                                           mst.Component.loc2 == pipette_index)).one()
        if task_id != None:
            task = session.exec(select(mst.TaskSchedule).where(mst.TaskSchedule.task_id == task_id)).one()
        check_out_action = mst.ComponentActionLog(status= None, occupancy= None, mutex= "Occupied", 
                                                  component= pipette)#, task_schedule = task)
        session.add(check_out_action)
        session.commit()

def check_out_needle(engine, needle_index, task_id):
    with Session(engine) as session:
        pipette = session.exec(select(mst.Component).where(mst.Component.loc0 == 9, 
                                                           mst.Component.loc2 == needle_index)).one()
        if task_id != None:
            task = session.exec(select(mst.TaskSchedule).where(mst.TaskSchedule.task_id == task_id)).one()
        check_out_action = mst.ComponentActionLog(status= None, occupancy= None, mutex= "Occupied", 
                                                  component= pipette)#, task_schedule = task)
        session.add(check_out_action)
        session.commit()

def update_vial_rack(engine, address, task_id, occupancy, mutex):
    with Session(engine) as session:
        component = session.exec(select(mst.Component).where(mst.Component.loc0 == 1, 
                                                             mst.Component.loc1 == address[1], 
                                                             mst.Component.loc2 == address[2])).one()
        if task_id != None:
            task = session.exec(select(mst.TaskSchedule).where(mst.TaskSchedule.task_id == task_id))
        else:
            task = None
        vial_rack_action = mst.ComponentActionLog(status= None, occupancy= occupancy, mutex= mutex, 
                                                  component= component, task_schedule= task)
        session.add(vial_rack_action)
        session.commit()

def react_sample(engine, reactor_address, task_id_num):
    with Session(engine) as session:
        # sample = session.exec(select(mst.SampleInfo).where(mst.SampleInfo.sample_id == sample_id)).one()
        if reactor_address[0] == 4:
            reactor = session.exec(select(mst.Component).where(mst.Component.loc0 == reactor_address[0], 
                                                               mst.Component.loc1 == reactor_address[1], 
                                                               mst.Component.loc2 == reactor_address[2])).one()
            task = session.exec(select(mst.TaskSchedule).where(mst.TaskSchedule.id == task_id_num)).one()
            sample = task.sample
            reactor_action = mst.ComponentActionLog(status= "Closed", occupancy= sample.sample_id, mutex= "Occupied", 
                                                    component= reactor, task_schedule= task)
            session.add(reactor_action)
            task_action = mst.TaskAction(task_status= "Loading", sample= sample, 
                                         component= reactor, task_schedule= task)
            session.add(task_action)
            sample_location = mst.SampleLocation(component_location= reactor, sample= sample, task_schedule= task)
            session.add(sample_location)
            session.commit()
        else:
            Exception("Wrong address for reactor")

def start_reactor(engine, reactor_address, task_id_num):
    with Session(engine) as session:
        # sample = session.exec(select(mst.SampleInfo).where(mst.SampleInfo.sample_id == sample_id)).one()
        if reactor_address[0] == 4 and reactor_address[2] == None:
            reactor = session.exec(select(mst.Component).where(mst.Component.loc0 == reactor_address[0], 
                                                               mst.Component.loc1 == reactor_address[1], 
                                                               mst.Component.loc2 == reactor_address[2])).one()
            task = session.exec(select(mst.TaskSchedule).where(mst.TaskSchedule.id == task_id_num)).one()
            reactor_action = mst.ComponentActionLog(status= "Closed", occupancy= None, mutex= "Occupied", 
                                                    component= reactor, task_schedule= task)
            session.add(reactor_action)
            task_action = mst.TaskAction(task_status= "Reacting", sample= None, 
                                         component= reactor, task_schedule= task)
            session.add(task_action)
            session.commit()
        else:
            Exception("Wrong address for reactor")

def create_system_db_from_SQL(engine):
    with Session(engine) as session:
        from src.system_db_setup import system_db

        # If a pipette or needle component is set to occupied, then it must have been used and disposed of.
        pipette_uses = session.exec(select(mst.ComponentActionLog).join(mst.Component)
                                    .where(mst.Component.loc0 == 8, mst.ComponentActionLog.mutex == "Occupied"))
        for use in pipette_uses:
            pipette_index = use.component.loc2
            # 'fresh_pipette' array split into 3 groups of 16
            # The array 'pipette_array' gives the indices for each pipette_index
            indices = np.where(system_db["pipette_array"] == pipette_index)
            if system_db["fresh_pipettes"][indices] != 0:
                system_db["fresh_pipettes"][indices] = 0
            else:
                Exception("WARNING, ASSIGNED THE SAME PIPETTE TWICE IN SQL")

        needle_uses = session.exec(select(mst.ComponentActionLog).join(mst.Component)
                                   .where(mst.Component.loc0 == 9, mst.ComponentActionLog.mutex == "Occupied"))
        for use in needle_uses:
            needle_index = use.Component.loc2
            # fresh_needles array split into 3 groups of 16
            # The array 'needle_array' gives the indices for each needle_index
            indices = np.where(system_db["needle_array"] == needle_index)
            if system_db["fresh_needles"][indices] != 0:
                system_db["fresh_needles"][indices] = 0
            else:
                Exception("WARNING, ASSIGNED THE SAME NEEDLE TWICE IN SQL")

        # Use the ComponentActionLog table to create the loaded_rack and rack_assignments arrays for the vials
        rack_movements = session.exec(select(mst.ComponentActionLog).join(mst.Component)
                                      .order_by(mst.ComponentActionLog.timestamp).where(mst.Component.loc0 == 1))
        for move in rack_movements:
            rack_index = move.component.loc2
            # Check if left or right vial rack
            if move.component.loc1 == 0:
                # Get the indices of the vial in the rack arrays
                indices = np.where(system_db["vial_rack_left_array"] == rack_index)
                if move.occupancy == "Empty":
                    system_db["loaded_rack_left"][indices] = 0
                    system_db["left_rack_assignments"][indices] = move.occupancy
                else:
                    system_db["loaded_rack_left"][indices] = 1
                    system_db["left_rack_assignments"][indices] = move.occupancy
            else:
                indices = np.where(system_db["vial_rack_right_array"] == rack_index)
                if move.occupancy == "Empty":
                    system_db["loaded_rack_right"][indices] = 0
                    system_db['right_rack_assignments'][indices] = move.occupancy
                else:
                    system_db["loaded_rack_right"][indices] = 1
                    system_db['right_rack_assignments'][indices] = move.occupancy

        # Use the ComponentActionLog to update the gripper_occupied status.
        latest_gripper_action = session.exec(select(mst.ComponentActionLog).join(mst.Component)
                                       .order_by(mst.ComponentActionLog.timestamp.desc())
                                       .where(mst.Component.loc0 == 2)).first()
        if latest_gripper_action.occupancy == "Empty":
            system_db["gripper_occupied"] = False
        else:
            system_db["gripper_occupied"] = True

        # Use the ComponentActionLog to update the clamp_status status.
        latest_clamp_action = session.exec(select(mst.ComponentActionLog).join(mst.Component)
                                     .order_by(mst.ComponentActionLog.timestamp.desc())
                                     .where(mst.Component.loc0 == 3)).first()
        system_db["clamp_status"] = latest_clamp_action.status
        system_db["clamp_assignment"] = latest_clamp_action.occupancy

        # Sort to each reactor using the ComponentActionLog and Component address
        # Use ReactorUse, ReactionInstance, and ReactorTelemetry to update the reactor dictionary in the sample_db.
        reactor_actions = session.exec(select(mst.ComponentActionLog).join(mst.Component)
                                       .order_by(mst.ComponentActionLog.timestamp).where(mst.Component.loc0 == 4))
        
        for action in reactor_actions:
            comp = action.component
            if comp.loc2 == None:
                latest_telemetry = session.exec(select(mst.ReactorTelemetry).join(mst.Component)
                                         .order_by(mst.ReactorTelemetry.timestamp.desc())
                                         .where(mst.Component.loc1 == comp.loc1)).first()
                
                system_db["reactor"][comp.loc1]["Meas. Temperature (C)"] = latest_telemetry.temperature

                task = action.task_schedule
                if task != None:
                    print("TASK EXISTS, target temp: ", task.target_temp)
                    if task.task_type == "pre_heat_reactor":
                        system_db["reactor"][comp.loc1]["Set Temperature (C)"] = task.target_temp
                        system_db["reactor"][comp.loc1]["Temperature (C)"] = latest_telemetry.temperature
                    else:
                        system_db["reactor"][comp.loc1]["Set Temperature (C)"] = task.target_temp
                        system_db["reactor"][comp.loc1]["Temperature (C)"] = None
            else:
                system_db["reactor"][comp.loc1][comp.loc2]["Assignment"] = action.occupancy

        # For each element in the system_db key ring, find their associated component actions in the SQL table.
        # After that, assign their mutex to the key ring to get the most up to date mutex.
        for key in system_db["KeyRing"]:
            if key != "Arm&Clamp":
                latest_key_action = session.exec(select(mst.ComponentActionLog).join(mst.Component)
                                           .order_by(mst.ComponentActionLog.timestamp.desc())
                                           .where(mst.Component.name == key)).first()
            # The arm/gripper and clamp will always share the same mutex since if one is in use, the other cannot be used
            else:
                latest_key_action = session.exec(select(mst.ComponentActionLog).join(mst.Component)
                                           .order_by(mst.ComponentActionLog.timestamp.desc())
                                           .where(mst.Component.name == "Gripper")).first()
            
                system_db["KeyRing"][key] = latest_key_action.mutex

        return system_db

def create_Cu_BTC_sample_db_from_SQL(engine):
    with Session(engine) as session:
        # Get the unique batch numbers.
        batch_numbers = session.exec(select(mst.SampleInfo.batch_id)
                                          .order_by(mst.SampleInfo.batch_id).distinct())
        all_sample_db = {}
        # For each batch, create their sample_db.
        for batch_num in batch_numbers:
            sample_db = {}
            samples = session.exec(select(mst.SampleInfo).where(mst.SampleInfo.batch_id == batch_num))
            for sample in samples:
                # Get the latest location for the sample. 
                latest_location = session.exec(select(mst.SampleLocation).order_by(mst.SampleLocation.timestamp.desc())
                                        .where(mst.SampleLocation.sample_id == sample.id)).first()
                fluid_links = sample.fluid_links
                sub_database = {}
                sub_database["Sample ID"] = sample.sample_id

                comp_loc = latest_location.component_location
                sub_database["Address"] = np.array([comp_loc.loc0, comp_loc.loc1, comp_loc.loc2])

                # Create dummy array to put fluid order in.
                fluid_order = ["", "", ""]
                # Dictionary to put experimental volumes in
                experiment_volumes = {}
                for link in fluid_links:
                    fluid_name = link.fluid.key
                    fluid_order[link.order] = fluid_name
                    experiment_volumes[fluid_name] = np.float64(link.target_volume)
                    if fluid_name != "Solvent Mixture":
                        sub_database[f"Target {fluid_name} Concentration (mol/L)"] = np.float64(link.target_concentration)

                sub_database["Fluid Order"] = fluid_order
                sub_database["Experiment Volumes (mL)"] = experiment_volumes
                sub_database["Temperature (C)"] = np.float64(sample.target_reaction_temp)
                sub_database["Reaction Time (min)"] = np.float64(sample.target_reaction_time)
                sample_db[sample.sample_id] = sub_database
            all_sample_db[f"Batch {batch_num}"] = sample_db
        return all_sample_db

def create_fluid_db_from_SQL(engine):
    with Session(engine) as session:
        batch_numbers = session.exec(select(mst.FluidConfig.batch_id)
                                     .order_by(mst.FluidConfig.batch_id).distinct())
        all_fluid_db = {}
        for batch_num in batch_numbers:

            fluid_db = {}
            fluids = session.exec(select(mst.FluidConfig)
                                  .where(mst.FluidConfig.batch_id == batch_num))
            for fluid in fluids:
                sub_db = {}
                # Get the latest fluid event associated with the fluid.
                latest_event = session.exec(select(mst.FluidEventLog).join(mst.FluidConfig)
                                            .order_by(mst.FluidEventLog.timestamp.desc())
                                            .where(mst.FluidConfig.key == fluid.key)).first()
                print("LATEST FLUID EVENT: ", latest_event)
                sub_db["Fluid Name"] = fluid.name
                sub_db["Volume (mL)"] = latest_event.volume
                syringe_pump = fluid.component
                address = np.array([syringe_pump.loc0, syringe_pump.loc1, syringe_pump.loc2])
                sub_db["Address"] = address
                sub_db["Purged"] = latest_event.purge_status
                sub_db["Purg Vol."] = fluid.purge_volume
                sub_db["Empty threshold"] = fluid.empty_thresh
                sub_db["Concentration (mol/L)"] = fluid.concentration

                fluid_db[fluid.key] = sub_db
            all_fluid_db[f"Batch {batch_num}"] = fluid_db
        return all_fluid_db

def create_reactor_db_from_SQL(engine):
    with Session(engine) as session:
        reactor_uses = session.exec(select(mst.ReactorUse))
        reactors_required = []
        total_react_duration = []
        list_of_react_durations = []
        list_of_temperatures = []
        batch_ids = []
        for use in reactor_uses:
            reactors_required.append(use.component.loc1)
            total_react_duration.append(use.total_reaction_duration)
            temps = []
            durations = []
            reaction_instances = session.exec(select(mst.ReactionInstance)
                                              .where(mst.ReactionInstance.reactor_id == use.id))
            for instance in reaction_instances:
                temps.append(instance.reaction_temperature)
                durations.append(instance.reaction_duration)
            list_of_react_durations.append(temps)
            list_of_temperatures.append(durations)
            batch_ids.append(use.batch_id)

        reactors_required = np.array(reactors_required)
        total_react_duration = np.array(total_react_duration)
        #Initiallize a reaction dataframe
        reactor_df = pd.DataFrame()
        reactor_df["Reactor"] = reactors_required
        reactor_df["Total Reactor Duration (Ds)"] = total_react_duration
        reactor_df["Reactor Use (Ds)"] = list_of_react_durations #Needs to be a list
        reactor_df["Reactor Temperature (C)"] = list_of_temperatures #Needs to be a list

        #Convert the list objects to "objects" - allows for re-assigning these cells with a new list
        reactor_df['Reactor Use (Ds)'] = reactor_df['Reactor Use (Ds)'].astype("object")
        reactor_df['Reactor Temperature (C)'] = reactor_df['Reactor Temperature (C)'].astype("object")

        reactor_df['Batch Number'] = batch_ids

        return reactor_df

def create_unitops_db_from_SQL(engine):
    with Session(engine) as session:
        header = ["Sample Name", "UnitOP", "Duration (Ds)", "Reactor", 
                  "Reactor Temperature (C)", "Batch Number", "Status", 
                  "Start Time (Ds)", "End Time (Ds)", "Resource", "Step"]
        unit_ops_df = pd.DataFrame(columns = header)
        tasks = session.exec(select(mst.TaskSchedule))
        for task in tasks:
            if task.sample != None:
                sample_key = task.sample.sample_id
            else:
                sample_key = None
            unit_op = task.task_type
            duration = task.duration
            reactor = task.reactor
            reactor_temp = task.target_temp
            batch_num = task.batch_id
            latest_action = session.exec(select(mst.TaskAction)
                                         .order_by(mst.TaskAction.timestamp.desc())
                                         .where(mst.TaskAction.task_schedule_id == task.id)).first()
            status = latest_action.task_status
            start_time = task.start_time_Ds
            end_time = task.end_time_Ds
            step = task.step

            component_name = task.component.name
            split_name = component_name.split("_")
            if split_name[0] == "Reactor":
                resource = f"Reactor {split_name[1]}"
            elif component_name == "Gripper":
                resource = "Arm&Clamp"
            elif component_name == "On_Vial_Rack":
                resource = "VialRack"
            elif component_name == "Centrifuge":
                resource = "Centrifuge"
            elif component_name == "Sonicator":
                resource = "Sonicator"
            else:
                Exception("Unable to parse component name: ", component_name)
                resource = None

            sub_df = pd.DataFrame([[sample_key, unit_op, duration, reactor, reactor_temp, 
                                    batch_num, status, start_time, end_time, resource, step]], columns = header)
            unit_ops_df = pd.concat([unit_ops_df, sub_df])
        return unit_ops_df
    
def create_db_from_SQL(engine):
    with Session(engine) as session:
        create_system_db_from_SQL(engine)
        create_Cu_BTC_sample_db_from_SQL(engine)
        create_fluid_db_from_SQL(engine)
        create_reactor_db_from_SQL(engine)
        create_unitops_db_from_SQL(engine)

def main():
    # Cu_BTC Experiment
    print("Initializing local databases")
    experiment = Cu_BTC()
    batch_id = 0
    engine = initialize_SQL_tables()
    initialize_component_table(engine)
    initialize_fluids(engine, experiment.fluid_db, batch_id)
    initialize_component_actions(engine)
    #initialize_fluid_events(engine)
    initialize_session_history(engine, batch_id)
    initialize_lab_telemetry(engine)
    create_new_batch(engine, experiment.sample_db, batch_id)
    #initialize_sample_locations(engine)
    check_out_pipette(engine, 28, None)
    update_vial_rack(engine, address= [1, 0, 1], task_id= None, 
                     occupancy= "Unassigned", mutex= "Available")
    system_db = create_system_db_from_SQL(engine)
    print("SYSTEM DB: ", system_db)

if __name__ == "__main__":
    main()
    