# src/coffeeeplot/atomic_telemetry.py
from __future__ import annotations
import json
import os
import uuid
from pathlib import Path
import logging

logger = logging.getLogger(__name__)    

from coffeeplot.plot_boundary import Observation, SeriesMemory, SeriesDefinition
from coffeeplot.plot_buffer import PlotBuffer
from coffeeplot.context import DATABASE_DIR

DEFAULT_TELEMETRY_LOG = DATABASE_DIR / "telemetry_log.jsonl"

class AtomicTelemetryLogger:
    """
    Maintains a robust, append-only disk record of incoming Observations.
    Utilizes line-buffered writes to guarantee persistence without corruption.
    Should consume Series Definiton
    """
    def __init__(self, filepath: str | Path) -> None:
        self.filepath = Path(filepath).expanduser().resolve()
        self.series_definitions: dict[uuid.UUID, SeriesDefinition]={}
        self.ensurepath()
    
    def ensurepath(self):
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        
    def register_series_definition(self,series_definition:SeriesDefinition) -> None:
        self.series_definitions[series_definition.uuid] = series_definition

    def consume_observation(self, series_uuid: uuid.UUID, obs: Observation) -> None:
        """
        Appends a single observation row atomically.
        Using write + flush ensures that OS-level buffering does not delay physical disk synchronization.
        """
        # Package a flat structure to minimize disk overhead
        # are you sure? the key will be duplicated every write
        log_entry = {
            "uuid": str(series_uuid), 
            "t": obs.timestamp, # required value
            "v": obs.value,
            "idx": obs.index,
            #**obs.annotation # we expect no annotation at write
        }
        
        # Open in append mode, write a single line, and flush immediately
        with open(self.filepath, "a", encoding="utf-8", buffering=1) as f:
            f.write(json.dumps(log_entry) + "\n")
            f.flush()
            os.fsync(f.fileno())  # Force OS to flush buffer cache to physical media


# ---
def run_telemetry_demo():
    # run_telemetry.py
    import time
    #from pipeline_eds.schema import Observation
    #from pipeline_eds.logger import AtomicTelemetryLogger

    # 1. Spin up components
    series_definition_flow = SeriesDefinition(label = "flow_rate_0", unit = "MGD", display_label = "Influent Flow Rate")
    series_definition_temp = SeriesDefinition(label = "temperature_0", unit = "deg F", display_label = "Atmospheric Temp")

    disk_logger = AtomicTelemetryLogger(filepath = DEFAULT_TELEMETRY_LOG)

    disk_logger.register_series_definition(series_definition_flow)
    disk_logger.register_series_definition(series_definition_temp)

    ui_buffer = PlotBuffer(title="Live Process Monitoring")

    # Pre-register our high-speed windows
    ui_buffer.register_series_definition(series_definition_flow, max_len = 50)
    ui_buffer.register_series_definition(series_definition_temp, max_len = 50)

    # in case you are in a special static limied data situation
    print(f"{series_definition_flow=}")
    series_memory_flow = SeriesMemory(series_definition_flow)
    series_memory_temp = SeriesMemory(series_definition_temp)

    # 2. Simulated Live Data Stream
    #while True:
    for _ in range(3):
        # Simulating sensor acquisition
        sensor_value_flow = 24.5 + (time.time() % 10) * 0.1
        sensor_value_temp = 999 + (time.time() % 10) * 0.2
        
        # STEP A: Persistence (Write to disk immediately - zero loss risk)
        obs_flow = Observation(value=sensor_value_flow, timestamp=time.time())
        obs_temp = Observation(value=sensor_value_temp, timestamp=time.time())

        disk_logger.consume_observation(series_definition_flow.uuid,obs_flow)
        disk_logger.consume_observation(series_definition_temp.uuid,obs_temp)
        
        # STEP B: Volatile UI buffer (Consume & discard old points out of memory)
        ui_buffer.consume_observation(series_definition_flow.uuid, obs_flow)
        ui_buffer.consume_observation(series_definition_temp.uuid, obs_temp)
    
        # Step C (don't do this, unless you are bulding a static plot with limited data)
        # uncommente to troubleshoot
        series_memory_flow.consume_observation(obs_flow)# the rich man's .append()
        series_memory_temp.consume_observation(obs_temp)# the rich man's .append()
        
        # Step C: The Web-Server / Dashboard polls this method to refresh charts
        plotly_data = ui_buffer.to_plotly_traces()
        
        time.sleep(1.0)

if __name__ == "__main__":
    run_telemetry_demo()
