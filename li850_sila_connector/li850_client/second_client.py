import asyncio

from sila.client import Client, ClientConfig


async def main():
    config = ClientConfig(
        hostname="127.0.0.1", port=5555, tls=False, default_timeout=5000
    )
    # Opens the connection, loads features, and closes the client on exit.
    async with Client(config) as client:
        print("Connected to:", await client.SiLAService.ServerName.read())
        yes = client.SimpleReturnYes2
        print(yes)
        gas_env = client.GasEnvironment

        print("Passed above")
        print(await gas_env.Co2.read())
        #tutorial = client.SiLAEndpointTutorialService
        #print("Number:", await tutorial.Number.read())
        #result = await tutorial.ParameterExample(Seed=42)
        #print("Result:", result.RandomNumber)


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(main(), timeout=20))