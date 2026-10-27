from sila import UnitComponent
from unitelabs.cdk import sila

CELSIUS = sila.constraints.Unit(
    label= " °C",
    components= [sila.constraints.UnitComponent(sila.constraints.SIUnit.KELVIN)],
    offset= -273.15,
)

KPA  = sila.constraints.Unit(
    label= "kPa",
    components= [sila.constraints.UnitComponent(sila.constraints.SIUnit.KILOGRAM), 
                 sila.constraints.UnitComponent(sila.constraints.SIUnit.METER), 
                 sila.constraints.UnitComponent(sila.constraints.SIUnit.SECOND, -2)],
    factor= 1 / 1000,
)

MILIMOL_PER_MOL= sila.constraints.Unit(
    label= "mmol/mol",
    components= [sila.constraints.UnitComponent(sila.constraints.SIUnit.DIMENSIONLESS)],
    factor= 1000,
)

MICROMOL_PER_MOL= sila.constraints.Unit(
    label= "μmol/mol",
    components= [sila.constraints.UnitComponent(sila.constraints.SIUnit.DIMENSIONLESS)],
    factor= 1e6,
)

# MILIMOL_PER_MOL= sila.constraints.Unit(
#     label= "mmol/mol",
#     components= [sila.constraints.UnitComponent(sila.constraints.SIUnit.MOLE), 
#                  sila.constraints.UnitComponent(sila.constraints.SIUnit.MOLE, -1)],
#     factor= 1000,
# )

# MICROMOL_PER_MOL= sila.constraints.Unit(
#     label= "μmol/mol",
#     components= [sila.constraints.UnitComponent(sila.constraints.SIUnit.MOLE), 
#                  sila.constraints.UnitComponent(sila.constraints.SIUnit.MOLE, -1)],
#     factor= 1e6,
# )