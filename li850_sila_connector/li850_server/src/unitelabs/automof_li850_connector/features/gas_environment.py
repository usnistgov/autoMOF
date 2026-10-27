import typing
import asyncio

from unitelabs.automof_li850_connector.io.errors import NotOkException
from unitelabs.cdk import sila


from ..io.protocol import AutomofLi850ConnectorProtocol

from ..io.units import CELSIUS, KPA, MICROMOL_PER_MOL, MILIMOL_PER_MOL
from ..io.gas_analyzer_return_types import Gas_Environment_Return_Types as gert

print("Message123")
class GasEnvironment(sila.Feature):    
    """Control and monitor the device."""

    def __init__(self):
        super().__init__(
            name= "GasEnvironment",
            originator="io.unitelabs",
            category="example",
        )
        self.protocol = AutomofLi850ConnectorProtocol()
        
        
    @sila.UnobservableProperty(name= "CO2")
    async def get_co2(self) -> typing.Annotated[float, MICROMOL_PER_MOL]:
        return await self.protocol.get_co2()
    
    @sila.UnobservableProperty(name= "H2O")
    async def get_h2o(self) -> typing.Annotated[float, MILIMOL_PER_MOL]:
        return await self.protocol.get_h2o()
    
    @sila.UnobservableProperty()
    async def get_temperature(self) -> typing.Annotated[float, CELSIUS]:
        return await self.protocol.get_temperature()
    
    @sila.UnobservableProperty()
    async def get_pressure(self) -> typing.Annotated[float, KPA]:
        return await self.protocol.get_pressure()

    @sila.ObservableProperty()
    async def subscribe_all_data(self) -> sila.Stream[gert]:
        while True:
            data = await self.protocol.subscribe_all_data()
            out = gert(data[0], data[1], data[2], data[3])
            yield out
            await asyncio.sleep(1)