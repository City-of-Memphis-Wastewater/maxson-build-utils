# src/coffeeplot/plot_buffer.py
from collections import deque
from dataclasses import dataclass, field
import uuid
from coffeeplot.plot_boundary import Observation, SeriesDefinition

@dataclass
class SeriesBuffer:
    """
    Consumes live Observation instances. Keeps a sliding window
    of coordinates capped at max_len for high-rate visual rendering.
    A series held in memory but adding new points and disposing of older points, for the purpose of plotting.
    """
    display_label: str
    unit: str | None = None
    max_len: int = 1000
    
    # Fast, thread-safe double-ended queues for coordinate tracking
    _timestamps: deque[float] = field(init=False)
    _values: deque[float] = field(init=False)

    def __post_init__(self) -> None:
        self._timestamps = deque(maxlen=self.max_len)
        self._values = deque(maxlen=self.max_len)

    def consume(self, obs: Observation) -> None:
        """Consumes an observation, extracts plotting vectors, and drops the rest."""
        self._timestamps.append(obs.timestamp)
        self._values.append(obs.value)

    def get_coordinates(self) -> tuple[list[float], list[float]]:
        return list(self._timestamps), list(self._values)


class PlotBuffer:
    """
    A live collection of SeriesBuffers mapped to trace structures.
    This acts as the active 'hopper' for dynamic visual manifestations.
    """
    def __init__(self, title: str = "Live Telemetry") -> None:
        self.title = title
        self.series_definitions: dict[uuid.UUID, SeriesDefinition]={}
        self.series_buffers: dict[uuid.UUID, SeriesBuffer] = {}

    def register_series_definition(self, series_definition: SeriesDefinition, max_len: int = 1000) -> None:
        self.series_definitions[series_definition.uuid] = series_definition
        self.series_buffers[series_definition.uuid] = SeriesBuffer(
            display_label=series_definition.display_label,
            unit=series_definition.unit,
            max_len=max_len
        )

    def consume_observation(self, series_uuid: uuid.UUID, obs: Observation) -> None:
        """Pushes data straight into the plotting engine deque."""
        if series_uuid in self.series_buffers:
            self.series_buffers[series_uuid].consume(obs)

    def to_plotly_traces(self) -> list[dict]:
        """
        Generates raw dictionary payloads ready for Plotly's extendTraces API.
        Assumes time is x and magnitude of series is y; alternatives are possible.
        """
        traces = []
        for key, buf in self.series_buffers.items():
            x, y = buf.get_coordinates()
            traces.append({
                "name": buf.display_label,
                "type": "scatter",
                "mode": "lines+markers",
                "x": x,
                "y": y,
                "meta": {"unit": buf.unit, "uuid": key}
            })
        return traces
