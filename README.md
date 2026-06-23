# NIST autoMOF

This repositiory containts the code base for the NIST autoMOF platform for the autonomous synthesis of Metal-Organic Frameworks (MOFs). 

The autonomous operation of MOF synthesis experiments is achieved through the Unit Operations (UnitOPs).
The list of experiments requested from some external source is passed to the autonomous scheduler that discovers optimal schedules for the UnitOPs.
The optimal schedules are discoved by a Job Shop Problem with a Constraint Satisfaction Solver, which is implemented using `ortools`.
These are then executed using a system of status dependencies for each sample and each robotic component, which is implmented using `asyncio`.

---

## Development

This code base is under active development

## Coorespondence 
Austin McDannald \
austin.mcdaannald@nist.gov \
National Institute of Standards and Technology
