import typing

from unitelabs.automof_li850_connector.io.errors import NotOkException
from unitelabs.cdk import sila

if typing.TYPE_CHECKING:
    from ..io.protocol import AutomofLi850ConnectorProtocol


class DeviceController(sila.Feature):
    """Control and monitor the device."""

    def __init__(self, protocol: "AutomofLi850ConnectorProtocol"):
        super().__init__(
            originator="io.unitelabs",
            category="example",
        )
        self.protocol = protocol

        @sila.UnobservableProperty()
        async def get_health(self) -> bytes:
            """
            Raises:
                NotOkException: Something has gone wrong with the analyzer
            """

            return await self.protocol.get_health(timeout=5)