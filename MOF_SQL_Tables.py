from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select
from datetime import UTC, datetime

class Component(SQLModel, table= True):
    id: int | None = Field(default = None, primary_key = True)
    name: str = Field(index = True)
    loc0: int = Field(index = True) # loc0-2 are based on zipcode system for components
    loc1: int | None = Field(index = True)
    loc2: int | None = Field(index = True)

    comp_actions: list["ComponentActionLog"] = Relationship(back_populates= "component")
    reactor_uses: list["ReactorUse"] = Relationship(back_populates= "component")
    task_actions: list["TaskAction"] = Relationship(back_populates= "component")
    task_schedule: list["TaskSchedule"] = Relationship(back_populates= "component")
    reactor_telemetry: list["ReactorTelemetry"] = Relationship(back_populates= "reactor")
    samples: list["SampleInfo"] = Relationship(back_populates= "component_location")
    # Nullable foreign key. Will be null if component is not syringe pump (loc0 = 5)
    # fluid_config_id: int | None = Field(default = None, foreign_key = "fluidconfig.id") 
    fluid_config: "FluidConfig" = Relationship(back_populates="component")

class FluidConfigSampleInfoLink(SQLModel, table= True):
    fluid_id: int | None = Field(default= None, foreign_key= "fluidconfig.id", primary_key= True)
    sample_id: int | None = Field(default= None, foreign_key= "sampleinfo.id", primary_key= True)

    fluid: "FluidConfig" = Relationship(back_populates= "sample_links")
    sample: "SampleInfo" = Relationship(back_populates= "fluid_links")

    order: int
    target_volume: float
    measured_weight: float | None = Field(default= None)
    target_concentration: float | None

class FluidConfig(SQLModel, table= True):
    id: int | None = Field(default = None, primary_key = True)
    key: str = Field(index= True)
    name: str = Field(index= True)
    formula: str
    empty_thresh: float
    purge_volume: float
    # component holds the address of the syringe pump associated with the fluid
    component_id: int = Field(foreign_key= "component.id")
    component: "Component" = Relationship(back_populates= "fluid_config")

    fluid_events: list["FluidEventLog"] = Relationship(back_populates= "fluid")
    sample_links: list[FluidConfigSampleInfoLink] = Relationship(back_populates= "fluid")

class FluidEventLog(SQLModel, table = True):
    id: int | None = Field(default = None, primary_key = True)
    timestamp: datetime = Field(default_factory= lambda: datetime.now(UTC), index= True)
    purge_status: bool
    volume: float

    fluid_id: int = Field(foreign_key= "fluidconfig.id")
    fluid: FluidConfig = Relationship(back_populates= "fluid_events")

class ComponentActionLog(SQLModel, table= True):
    id: int | None = Field(default = None, primary_key = True)
    timestamp: datetime = Field(default_factory= lambda: datetime.now(UTC), index= True)
    status: str | None = Field(index = True)
    occupancy: str | None = Field(index = True)
    mutex: str = Field(index = True)

    component_id: int = Field(foreign_key= "component.id")
    component: Component = Relationship(back_populates= "comp_actions")
    # Component actions may not be associated with a specific task, such as when the component action table is first initialized
    task_schedule_id: int | None = Field(default = None, foreign_key= "taskschedule.id")
    task_schedule: TaskSchedule = Relationship(back_populates= "comp_actions")

# A single contiguous run of the MOF robot, NOT spanning multiple campaigns. 
# Only one session can be active at a time.
# If a crash occurs, the cause should be logged and a new session should be started
class SessionHistory(SQLModel, table= True):
    id: int | None = Field(default = None, primary_key = True)
    campaign_id: str = Field(index = True)
    batch_id: str = Field(index = True)
    batch_status: str | None
    start_time: float = Field(index = True)
    end_time: float | None = Field(default = None, index = True)
    end_report: str | None = Field(default = None)

    #tasks: list[Task] = Relationship(back_populates= "robot_sessions", link_model= TaskRobotSessionLink)

class LabTelemetry(SQLModel, table= True):
    id: int | None = Field(default = None, primary_key = True)
    timestamp: datetime = Field(default_factory= lambda: datetime.now(UTC), index= True)
    temperature: float
    humidity: float

class SampleInfo(SQLModel, table= True):
    id: int | None = Field(default = None, primary_key = True)
    sample_id: str = Field(index = True) # Contains the 4 letter id for the single sample to be sythesized.
    barcode: str = Field(index = True)
    formula: str
    empty_weight: float | None = Field(default = None) # Will get updated when empty weight is measured
    #status: str # Could potentially be a pointer to the active status instead?
    target_reaction_time: float
    target_reaction_temp: float

    component_id: int = Field(foreign_key = "component.id")
    component_location: Component = Relationship(back_populates= "samples")
    fluid_links: list[FluidConfigSampleInfoLink] = Relationship(back_populates= "sample")
    sample_locations: list["SampleLocation"] = Relationship(back_populates= "sample")
    task_actions: list["TaskAction"] = Relationship(back_populates= "sample")
    task_schedule: list["TaskSchedule"] = Relationship(back_populates= "sample")

class SampleLocation(SQLModel, table= True):
    id: int | None = Field(default = None, primary_key = True)
    location: str = Field(index = True)
    timestamp: datetime = Field(default_factory= lambda: datetime.now(UTC), index= True)

    sample_id: int = Field(foreign_key = "sampleinfo.id")
    sample: SampleInfo = Relationship(back_populates= "sample_locations")
    # Tasks associated with the Sample Locations are initially None
    task_schedule_id: int | None = Field(default= None, foreign_key= "taskschedule.id")
    task_schedule: TaskSchedule = Relationship(back_populates= "sample_locations")

class ReactorUse(SQLModel, table= True):
    id: int | None = Field(default = None, primary_key = True)
    batch_id: int = Field(index = True)
    total_reaction_duration: float

    component_id: int = Field(default= None, foreign_key= "component.id")
    component: Component = Relationship(back_populates= "reactor_uses")
    reaction_instances: list["ReactionInstance"] = Relationship(back_populates= "reactor")

class ReactionInstance(SQLModel, table= True):
    id: int | None = Field(default = None, primary_key = True)
    order: int
    reaction_duration: float
    reaction_temperature: float

    reactor_id: int = Field(foreign_key = "reactoruse.id")
    reactor: ReactorUse = Relationship(back_populates= "reaction_instances")

class TaskSchedule(SQLModel, table= True):
    id: int | None = Field(default = None, primary_key = True)
    campaign_id: str = Field(index = True)
    job_id: str = Field(index = True)
    job_type: str
    # sample_id: str | None = Field(index = True)
    # component_id: str  # Could replace with a reference to the actual component
    task_id: str
    task_type: str
    reactor: str | None
    target_temp: float | None
    start_time_Ds: float = Field(index = True)
    end_time_Ds: float = Field(index = True)

    sample_id: int | None = Field(foreign_key = "sampleinfo.id")
    sample: SampleInfo = Relationship(back_populates= "task_schedule") 
    component_id: int = Field(foreign_key= "component.id")
    component: Component = Relationship(back_populates= "task_schedule")
    comp_actions: list["ComponentActionLog"] = Relationship(back_populates = "task_schedule")
    sample_locations: list["SampleLocation"] = Relationship(back_populates = "task_schedule")
    task_actions: list["TaskAction"] = Relationship(back_populates = "task_schedule")

class TaskAction(SQLModel, table= True):
    id: int | None = Field(default = None, primary_key = True)
    timestamp: datetime = Field(default_factory= lambda: datetime.now(UTC), index= True)
    task_status: str

    sample_id: int | None = Field(foreign_key = "sampleinfo.id")
    sample: SampleInfo = Relationship(back_populates= "task_actions")
    component_id: int = Field(foreign_key= "component.id")
    component: Component = Relationship(back_populates= "task_actions")
    task_schedule_id: int = Field(foreign_key= "taskschedule.id")
    task_schedule: TaskSchedule = Relationship(back_populates= "task_actions")

class ReactorTelemetry(SQLModel, table= True):
    id: int | None = Field(default = None, primary_key = True)
    timestamp: datetime = Field(default_factory= lambda: datetime.now(UTC), index= True)
    temperature: float
    reactor_id: int = Field(foreign_key= "component.id")
    reactor: Component = Relationship(back_populates= "reactor_telemetry")

def start_engine(sqlite_file_name):
    sqlite_url = f"sqlite:///{sqlite_file_name}"

    engine = create_engine(sqlite_url, echo=False)
    return engine

def create_db_and_tables(engine):
    SQLModel.metadata.create_all(engine)

def main():
    sqlite_file_name = "SQL Files/MOF_database4.db"
    engine = start_engine(sqlite_file_name)
    create_db_and_tables(engine)

if __name__ == "__main__":
    main()
        
