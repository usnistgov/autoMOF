from typing import NamedTuple, Annotated

from .units import CELSIUS, KPA, MICROMOL_PER_MOL, MILIMOL_PER_MOL

class Gas_Environment_Return_Types(NamedTuple):
    TEMPERATURE: Annotated[float, CELSIUS]
    PRESSURE: Annotated[float, KPA]
    CO2_CONCENTRATION: Annotated[float, MICROMOL_PER_MOL]
    H2O_CONCENTRATION: Annotated[float, MILIMOL_PER_MOL]