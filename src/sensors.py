"""Sensor nodes: the abstract base, the five real sensors, and a wireless one.

SensorNode is an ABC - it handles the shared stuff (id validation, calibration,
self-test) and leaves sensor_id and read() for subclasses. The five concrete
nodes only differ in their range, unit and alarm threshold, so the actual
read() simulation lives once in the base as a helper. WirelessSensorNode mixes
in a battery using cooperative multiple inheritance.
"""

import re
import random
from abc import ABC, abstractmethod
from datetime import datetime

from src.readings import SensorReading
from src.exceptions import CalibrationError, SensorOfflineError
from src.alerts import Alert


class SensorNode(ABC):
    """Common behaviour for every sensor in the network.

    Subclasses provide a sensor_id (it's an abstract property) and a read().
    Everything else - id-format checks, the validated calibration offset, the
    self-test - is shared here.
    """

    # SN-TTTT-NN : 4-letter type code, 2-digit number, e.g. SN-TEMP-01
    _ID_PATTERN = re.compile(r"^SN-[A-Z]{4}-\d{2}$")

    def __init__(self, sensor_id: str, location: str, unit: str,
                 safe_min: float, safe_max: float,
                 calibration_offset: float = 0.0, **kwargs) -> None:
        # pass anything we don't recognise further up the MRO (battery kwargs,
        # in the wireless case) so multiple inheritance keeps working
        super().__init__(**kwargs)
        if not self._ID_PATTERN.match(sensor_id):
            raise ValueError(
                f"bad sensor_id {sensor_id!r}; expected SN-TTTT-NN, e.g. SN-TEMP-01")
        self._sensor_id = sensor_id
        self.location = location
        self.unit = unit
        self.safe_min = float(safe_min)
        self.safe_max = float(safe_max)
        self._calibration_offset = 0.0
        self.calibration_offset = calibration_offset  # run it through the setter

    @property
    @abstractmethod
    def sensor_id(self) -> str:
        """Unique id of this sensor (subclasses expose the stored value)."""

    @abstractmethod
    def read(self) -> SensorReading:
        """Take one reading and wrap it in a SensorReading."""

    @property
    def calibration_offset(self) -> float:
        """Offset added to every raw reading. Capped at +/-10% of full scale."""
        return self._calibration_offset

    @calibration_offset.setter
    def calibration_offset(self, value: float) -> None:
        limit = 0.10 * (self.safe_max - self.safe_min)
        if abs(value) > limit:
            raise CalibrationError(
                self._sensor_id,
                f"offset {value} is outside +/-{limit:.3f} (10% of full scale)")
        self._calibration_offset = float(value)

    def calibrate(self, offset: float) -> None:
        """Re-calibrate. Goes through the property so the same check applies."""
        self.calibration_offset = offset

    def self_test(self) -> bool:
        """Quick sanity check. Raises SensorOfflineError if it fails."""
        limit = 0.10 * (self.safe_max - self.safe_min)
        if abs(self._calibration_offset) > limit:
            raise SensorOfflineError(self._sensor_id, "self-test failed: offset drifted")
        return True

    def _simulate_reading(self, spike_probability: float = 0.1) -> SensorReading:
        """Make up a plausible reading - mostly in range, sometimes over alarm.

        The occasional spike is what gives the alert logic something to react
        to during a run. The offset is applied and the result is clamped to
        the sensor's physical limits.
        """
        alarm = getattr(self, "ALARM_THRESHOLD", self.safe_max)
        if random.random() < spike_probability:
            raw = random.uniform(alarm, self.safe_max)
        else:
            raw = random.uniform(self.safe_min, alarm)
        value = raw + self._calibration_offset
        value = max(self.safe_min, min(self.safe_max, value))
        return SensorReading(self.sensor_id, value, self.unit, datetime.now())

    def __str__(self) -> str:
        return f"{type(self).__name__}[{self.sensor_id}] @ {self.location}"

    def __repr__(self) -> str:
        return (f"{type(self).__name__}(sensor_id={self.sensor_id!r}, "
                f"location={self.location!r}, calibration_offset={self._calibration_offset!r})")


class TemperatureNode(SensorNode):
    """Industrial temperature probe, -40 to 150 C."""

    ALARM_THRESHOLD = 120.0

    def __init__(self, sensor_id: str, location: str, calibration_offset: float = 0.0) -> None:
        super().__init__(sensor_id, location, "°C", -40.0, 150.0, calibration_offset)

    @property
    def sensor_id(self) -> str:
        return self._sensor_id

    def read(self) -> SensorReading:
        return self._simulate_reading(spike_probability=0.08)


class PressureNode(SensorNode):
    """Pressure transducer, 0 to 10 bar."""

    ALARM_THRESHOLD = 9.0

    def __init__(self, sensor_id: str, location: str, calibration_offset: float = 0.0) -> None:
        super().__init__(sensor_id, location, "bar", 0.0, 10.0, calibration_offset)

    @property
    def sensor_id(self) -> str:
        return self._sensor_id

    def read(self) -> SensorReading:
        return self._simulate_reading()


class VibrationNode(SensorNode):
    """Vibration sensor reporting RMS velocity, 0 to 25 mm/s."""

    ALARM_THRESHOLD = 20.0

    def __init__(self, sensor_id: str, location: str, calibration_offset: float = 0.0) -> None:
        super().__init__(sensor_id, location, "mm/s", 0.0, 25.0, calibration_offset)

    @property
    def sensor_id(self) -> str:
        return self._sensor_id

    def read(self) -> SensorReading:
        return self._simulate_reading()


class GasConcentrationNode(SensorNode):
    """Combustible-gas sensor, 0 to 100% of the lower explosive limit."""

    ALARM_THRESHOLD = 20.0

    def __init__(self, sensor_id: str, location: str, calibration_offset: float = 0.0) -> None:
        super().__init__(sensor_id, location, "% LEL", 0.0, 100.0, calibration_offset)

    @property
    def sensor_id(self) -> str:
        return self._sensor_id

    def read(self) -> SensorReading:
        return self._simulate_reading()


class FlowRateNode(SensorNode):
    """Flow meter, 0 to 500 L/min."""

    ALARM_THRESHOLD = 450.0

    def __init__(self, sensor_id: str, location: str, calibration_offset: float = 0.0) -> None:
        super().__init__(sensor_id, location, "L/min", 0.0, 500.0, calibration_offset)

    @property
    def sensor_id(self) -> str:
        return self._sensor_id

    def read(self) -> SensorReading:
        return self._simulate_reading()


class BatteryPoweredMixin:
    """Gives a node a battery that drains a bit on every read.

    The __init__ is cooperative: it grabs its own two keyword args and forwards
    the rest up the chain with super(), so it can sit in a multiple-inheritance
    line-up without eating the other base's arguments.
    """

    def __init__(self, *args, battery_level: float = 100.0,
                 discharge_per_reading: float = 0.5, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._battery_level = 100.0
        self.battery_level = float(battery_level)  # validate via the setter
        self._discharge_per_reading = float(discharge_per_reading)
        self.pending_alerts = []  # battery alerts wait here until the hub drains them

    @property
    def battery_level(self) -> float:
        """Charge remaining, 0-100%."""
        return self._battery_level

    @battery_level.setter
    def battery_level(self, value: float) -> None:
        if not 0.0 <= value <= 100.0:
            raise ValueError(f"battery_level must be between 0 and 100, got {value}")
        self._battery_level = float(value)

    @property
    def is_low_battery(self) -> bool:
        """True once charge drops under 20%."""
        return self._battery_level < 20.0

    def discharge(self) -> None:
        """Spend one reading's charge. Queue a LOW alert the moment we go low."""
        was_low = self.is_low_battery
        self._battery_level = max(0.0, self._battery_level - self._discharge_per_reading)
        if self.is_low_battery and not was_low:
            who = getattr(self, "sensor_id", "UNKNOWN")
            self.pending_alerts.append(
                Alert(who, "LOW", f"battery low at {self._battery_level:.1f}%", datetime.now()))


class WirelessSensorNode(SensorNode, BatteryPoweredMixin):
    """A sensor that also runs off a battery.

    MRO: WirelessSensorNode -> SensorNode -> BatteryPoweredMixin -> object, so
    one super().__init__() runs both parents in turn (cooperative MI).
    """

    def __init__(self, sensor_id: str, location: str, unit: str,
                 safe_min: float, safe_max: float, calibration_offset: float = 0.0,
                 battery_level: float = 100.0, discharge_per_reading: float = 0.5) -> None:
        super().__init__(sensor_id, location, unit, safe_min, safe_max,
                         calibration_offset=calibration_offset,
                         battery_level=battery_level,
                         discharge_per_reading=discharge_per_reading)

    @property
    def sensor_id(self) -> str:
        return self._sensor_id

    def read(self) -> SensorReading:
        """Read like any node, then drain the battery a little."""
        reading = self._simulate_reading()
        self.discharge()
        return reading

    def __str__(self) -> str:
        return (f"WirelessSensorNode[{self.sensor_id}] @ {self.location} "
                f"(battery {self.battery_level:.0f}%)")

    def __repr__(self) -> str:
        return (f"WirelessSensorNode(sensor_id={self.sensor_id!r}, location={self.location!r}, "
                f"unit={self.unit!r}, battery_level={self.battery_level!r})")
