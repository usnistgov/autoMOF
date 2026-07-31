import asyncio
from typing import Dict

from sila2.server import ServerProtocol, Service, Method, Parameter, ReturnValue

import csv
from pathlib import Path
from datetime import datetime
import li850 as gas



# ---------------------------------------------------------------------------
# Helper functions – replace with real hardware access
# ---------------------------------------------------------------------------
gas.config()
data_result = gas.get_data()


def read_co2() -> float:
    """Read CO₂ concentration (μmol/mol)."""
    data = gas.get_data()
    return float(data.get("CO2")) if data else None

def read_h2o() -> float:
    """Read H₂O concentration (mmol/mol)."""
    data = gas.get_data()
    return float(data.get("H2O")) if data else None

def read_pressure() -> float:
    """Read pressure                                                                                                                                                                                                                                                                                                                                                                                                                                (kPa)."""
    data = gas.get_data()
    return float(data.get("Cell Press")) if data else None

def read_temperature() -> float:
    """Read temperature (°C)."""
    data = gas.get_data()
    return float(data.get("Cell Temp")) if data else None


# ---------------------------------------------------------------------------
# SiLA 2 Service definition
# ---------------------------------------------------------------------------
class CO2SensorService(Service):
    """SiLA 2 service exposing CO₂, H₂O, and temperature measurements."""

    @Method(
        name="GetMeasurements",
        description="Returns the current CO₂ level, H₂O and temperature.",
        parameters=[],
        returns=[
            ReturnValue(name="CO2",    type="float", description="CO₂ concentration in μmol/mol"),
            ReturnValue(name="H₂O", type="float", description="H₂O concentration in mmol/mol"),
            ReturnValue(name="Pressure", type="float", description="Pressure in kPa"),
            ReturnValue(name="Temperature", type="float", description="Temperature in °C")
        ]
    )
    async def get_measurements(self) -> Dict[str, float]:
        """Collect measurements from the sensor."""
        co2 = read_co2()
        h2o = read_h2o()
        pressure = read_pressure()
        temperature = read_temperature()
        return {"CO2": co2, "H₂O": h2o,"Pressure":pressure, "Temperature": temperature}

# ---------------------------------------------------------------------------
# Server protocol implementation
# ---------------------------------------------------------------------------
class CO2SensorServer(ServerProtocol):
    """SiLA 2 server that hosts the CO₂ sensor service."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5000):
        super().__init__(host=host, port=port, name="CO₂ Sensor")
        # Register the service
        self.add_service(CO2SensorService(self))

    async def _collect_measurements(self):
        """
        Collect CO₂, h2o and temperature every 20 ms for 1 minute,
        then write the results to a CSV file in the `data/` folder.
        """
        duration_s = 60                # 1 minute
        interval_s = 0.02              # 20 ms
        samples = int(duration_s / interval_s)

        # Prepare storage
        records = []  # each entry: (timestamp_iso, co2, h2o, temperature)

        for _ in range(samples):
            ts = datetime.utcnow().isoformat()
            co2 = read_co2()
            h2o = read_h2o()
            pres = read_pressure()
            temp = read_temperature()
            records.append((ts, co2, h2o, pres, temp))
            await asyncio.sleep(interval_s)

        # Ensure output directory exists
        out_dir = Path("data")
        out_dir.mkdir(parents=True, exist_ok=True)

        # Write CSV – filename includes start‑time for uniqueness
        start_ts = records[0][0].replace(":", "-")
        csv_path = out_dir / f"co2_sensor_{start_ts}.csv"

        with csv_path.open(mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp_utc", "co2_1e-6", "h2o_1e-3", "pressure_kpa", "temperature_C"])
            writer.writerows(records)

        print(f"Saved {len(records)} samples to {csv_path}")

    async def start(self):
        """Start the SiLA 2 server and launch the sampling task."""
        # Launch the periodic‑sampling coroutine *without* blocking the server
        asyncio.create_task(self._collect_measurements())

        await self.listen()
        print(f"SiLA 2 CO₂ sensor server listening on {self.host}:{self.port}")
        await asyncio.Future()  # keep running until cancelled

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    server = CO2SensorServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nServer stopped by user")