import typing

from unitelabs.bus.testing import create_mock_connection
from unitelabs.cdk.features.core.simulation_controller import SimulationControllerBase, StartRealModeFailed

from ...io.protocol import AutomofLi850ConnectorProtocol
from ...io.simulation import stubs


class SimulationController(SimulationControllerBase):
    """Switch the connector between simulated responses and the real device."""

    def __init__(
        self,
        protocol: AutomofLi850ConnectorProtocol,
        simulation_mode: bool = True,
    ):
        super().__init__()
        self.protocol = protocol
        self._og_identity = self.protocol.identity
        self._og_transport_factory = None
        self._og_transport_kwargs: dict = {}

        if simulation_mode:
            self._loop = asyncio.get_event_loop_policy().get_event_loop()
            asyncio.run_coroutine_threadsafe(self.start_simulation_mode(), self._loop)

    @typing.override
    async def simulation_mode(self) -> bool:
        return self._simulation_mode

    @typing.override
    async def start_real_mode(self) -> None:
        if self._simulation_mode:
            self.protocol.logger.info("Starting real mode.")

            if hasattr(self.protocol, "transport") and self.protocol.transport:
                self.protocol.transport.close()

            self.protocol.identity = self._og_identity

            if self._og_transport_factory is None:
                msg = "Cannot start real mode."
                raise StartRealModeFailed(msg)

            await self.protocol.connect(self._og_transport_factory, **self._og_transport_kwargs)

            await self.protocol.open()
            self._simulation_mode = False

    @typing.override
    async def start_simulation_mode(self) -> None:
        if self._simulation_mode:
            return

        self.protocol.logger.info("Starting simulation mode.")

        # Backup real identity (only used for serial communication, autoconnection)
        self._og_identity = self.protocol.identity
        self.protocol.identity = AsyncMock(return_value=True)

        if hasattr(self.protocol, "transport") and self.protocol.transport:
            self.protocol.transport.close()

        self._og_transport_factory, self._og_transport_kwargs = await self.protocol.connect(
            create_mock_connection, stubs=stubs
        )

        await self.protocol.open()
        self._simulation_mode = True