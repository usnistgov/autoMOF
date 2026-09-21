# NIST autoMOF

This repository contains the code base for the NIST autoMOF platform for the autonomous synthesis of Metal-Organic Frameworks (MOFs). 
The main goal of this platform is to map the synthesis landscapes of MOFs.
This codebase enables the autonomous operation of this robotic synthesis platform, scheduling then executing synthesis experiments in parallel. 

Each synthesis experiment is broken down into several tasks, which we term Unit Operations (UnitOPs).
The list of experiments requested from some external source is passed to the autonomous scheduler that discovers optimal schedules for the UnitOPs.
The optimal schedules are discovered by a Job Shop Problem with a Constraint Satisfaction Solver, which is implemented using `ortools`.
These are then executed using a system of status dependencies for each sample and each robotic component, which is implemented using `asyncio`.

For the implementation of the autonomous scheduler see [op_scheduler](./src/op_scheduler.py)
For the implementation of the system of dependencies and mutexes see [unit_operation](./src/unit_operation.py) for the sample-wise UnitOPs, and [system_db_setup](./src/system_db_setup.py) for the mutexes associated with the physical resources of the robotic platform. 

For the manuscript describing the use of this code base see: ["Optimal Resource Utilization for Autonomous Laboratory Orchestrators"](https://arxiv.org/abs/2607.01188).
For the pinned version of the codebase used in that manuscript see [release v0.0.2](https://github.com/usnistgov/autoMOF/releases/tag/v0.0.2).
Running [reschedule_test.py](https://github.com/usnistgov/autoMOF/blob/main/reschedule_test.py) will generate an example schedule of experiments, then it will generate an example of re-scheduling by introducing a new set of jobs and the remaining tasks of the previous jobs. 
The associated Gantt charts created in that script were used in Figure 1 and 2 of the manuscript for example scheduling and re-scheduling, respectively.
Running [schedule_scale_run.sh](https://github.com/usnistgov/autoMOF/blob/main/schedule_scale_run.sh) will run tests to show how the compute time for the schedule scales with the number of samples. 
This was done with 3 different configurations, each with a total allowable time of 600 mins:
1. [schedule_scale_test.py](https://github.com/usnistgov/autoMOF/blob/main/schedule_scale_test.py) searches for optimal schedules and uses decasecond time resolution.
2. [schedule_scale_test_hs.py](https://github.com/usnistgov/autoMOF/blob/main/schedule_scale_test_hs.py) searches for optimal schedules and uses hectosecond time resolution.
3. [schedule_scale_test_timebudget.py](https://github.com/usnistgov/autoMOF/blob/main/schedule_scale_test_timebudget.py) uses decasecond time resolution and keeps the best schedule discovered after 10 s of searching.
These scripts were used to generate the results shown in the Schedule Performance Scaling section of the Supplemental Information of the manuscript. 




---

## Development

This code base is under active development

## Coorespondence 
Austin McDannald \
austin.mcdaannald@nist.gov \
National Institute of Standards and Technology
