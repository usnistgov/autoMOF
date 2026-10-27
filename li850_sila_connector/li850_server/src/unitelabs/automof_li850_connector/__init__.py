import collections.abc
from importlib.metadata import version

from unitelabs.cdk import Connector
from unitelabs.cdk.features.core.lock_controller import LockController

from .config import AutomofLi850ConnectorConfig

from .features.device_controller import DeviceController
from .features import (
    SimpleReturnYes,
    GasEnvironment,
)
from .features.simple_functions2 import SimpleReturnYes2
from .io.protocol import AutomofLi850ConnectorProtocol
from .config import AutomofLi850ConnectorConfig


__version__ = version("unitelabs-automof-li850-connector")


async def create_app(config: AutomofLi850ConnectorConfig) -> collections.abc.AsyncGenerator[Connector, None]:
    """Create the connector application."""

    app = Connector(config)
    app.register(LockController())
    app.register(GasEnvironment())
    app.register(SimpleReturnYes())
    app.register(SimpleReturnYes2(name= "Simple yes 2"))
    print("Registered")
    yield app

