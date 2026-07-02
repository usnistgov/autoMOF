# NIST autoMOF

This repositiory containts the code base for the NIST autoMOF platform for the autonomous synthesis of Metal-Organic Frameworks (MOFs). 
The main goal of this platform is to map the synthesis landscapes of MOFs.
This codebase enables the autonomous operation of this robotic synthesis platform, scheduling then executing synthesis experiments in parallel. 

Each synthesis experiment is broken down into several tasks, which we term Unit Operations (UnitOPs).
The list of experiments requested from some external source is passed to the autonomous scheduler that discovers optimal schedules for the UnitOPs.
The optimal schedules are discoved by a Job Shop Problem with a Constraint Satisfaction Solver, which is implemented using `ortools`.
These are then executed using a system of status dependencies for each sample and each robotic component, which is implmented using `asyncio`.

For the implementation of the autonomous scheduler see [op_scheduler](./src/op_scheduler.py)
For the implementation of the system of dependencies and mutexes see [unit_operation](./src/unit_operation.py) for the sample-wise UnitOPs, and [system_db_setup](./src/system_db_setup.py) for the mutexes associated with the physical resources of the robotic platform. 

For the archived version of the code base used in the manuscript ["Optimal Resource Utilization for Autonomous Laboratory Orchestrators"](https://arxiv.org/abs/2607.01188), see [v0.0.1](https://github.com/usnistgov/autoMOF/releases/tag/v0.0.1).
For the script used to generate the figures in that manuscript see [reschedule_test.py](https://github.com/usnistgov/autoMOF/blob/684634cb0c7450671892d5b33d19e4aceffd017f/reschedule_test.py)

---

## Development

This code base is under active development

## Coorespondence 
Austin McDannald \
austin.mcdaannald@nist.gov \
National Institute of Standards and Technology
