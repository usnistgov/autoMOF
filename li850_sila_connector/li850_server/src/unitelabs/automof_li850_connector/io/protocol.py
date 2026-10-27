import typing

from unitelabs.bus import ByteCommand, Protocol, create_serial_connection

from .errors import NotOkException
from unitelabs.bus import Protocol, create_serial_connection, SerialCommand


protocol = Protocol(
    create_serial_connection,
    port='COM5',    # Replace with your port name, e.g. '/dev/cu.usbmodem3210' on macOS, 'COM3' on Windows
    #baudrate=9600,          # Set the baud rate to match your device
    #timeout=1,              # Set a timeout for read operations
)
class AutomofLi850ConnectorProtocol:
    """Underlying communication protocol for li850."""

    def __init__(self) -> None:
        self.calibrated= False

    async def serial_payload_config(self):
        await protocol.open()
        print("Done open")
        command = ("<li850><cfg><outrate>0</outrate></cfg>"
                "<rs232><co2>true</co2><flowrate>false</flowrate>"
                "<h2o>true</h2o><celltemp>true</celltemp>"
                "<cellpres>true</cellpres><ivolt>false</ivolt>"
                "<co2abs>false</co2abs><h2oabs>false</h2oabs>"
                "<h2odewpoint>false</h2odewpoint><raw>false</raw>"
                "<echo>false</echo><strip>true</strip></rs232></li850>\r\n")
        response = await protocol.execute(SerialCommand(command))
        print('Received response:', response)
        protocol.close()

    async def get_data(self) -> list:
        if not self.calibrated:
            await self.serial_payload_config()
            self.calibrated = True
        await protocol.open()
        #await self.serial_payload_config()
        command = ("<li850><data>?</data><rs232><strip>true</strip></rs232></li850>\r\n")
        response = await protocol.execute(SerialCommand(command))
        print('Received data:', response)
        protocol.close()
        array = response.split(" ")
        return array

    async def get_co2(self):
        output = await self.get_data()
        print("OUtput data type: ", output)
        return float(output[2])

    async def get_h2o(self):
        output = await self.get_data()
        return float(output[3])

    async def get_temperature(self):
        output = await self.get_data()
        return float(output[0])

    async def get_pressure(self):
        output = await self.get_data()
        return float(output[1])

    async def subscribe_all_data(self):
        output = await self.get_data()
        formatted_output = [float(output[0]), float(output[1]), float(output[2]), float(output[3])]
        return formatted_output


