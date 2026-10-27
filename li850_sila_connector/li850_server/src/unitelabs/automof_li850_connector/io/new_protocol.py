import asyncio

from unitelabs.bus import Protocol, create_serial_connection, SerialCommand

async def main():
    protocol = Protocol(
        create_serial_connection,
        port='COM5',    # Replace with your port name, e.g. '/dev/cu.usbmodem3210' on macOS, 'COM3' on Windows
        #baudrate=9600,          # Set the baud rate to match your device
        #timeout=1,              # Set a timeout for read operations
    )
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
    print('Received:', response)

    command = ("<li850><data>?</data><rs232><strip>true</strip></rs232></li850>\r\n")
    response = await protocol.execute(SerialCommand(command))
    print('Received2:', response)

    protocol.close()


if __name__ == "__main__":
    asyncio.run(main())