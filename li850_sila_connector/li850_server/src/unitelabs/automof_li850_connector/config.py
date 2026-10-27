import dataclasses
from importlib.metadata import version

from unitelabs.cdk import ConnectorBaseConfig, SiLAServerConfig

__version__ = version("unitelabs-automof-li850-connector")


@dataclasses.dataclass
class AutomofLi850ConnectorConfig(ConnectorBaseConfig):
    """Configuration for the li850."""

    simulation_mode: bool = False
    """Whether to start the connector in simulation mode, without hardware."""
    
    sila_server: SiLAServerConfig = dataclasses.field(
        default_factory=lambda: SiLAServerConfig(
            name="li850",
            type="Example",
            hostname="127.0.0.1",
            description=(
                """
                Now without WSL!
                """
            ),
            version=str(__version__),
            vendor_url="https://unitelabs.io/",
        )
    )
