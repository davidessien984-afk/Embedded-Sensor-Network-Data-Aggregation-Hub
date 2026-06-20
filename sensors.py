"""
src/sensors.py (TemperatureNode section)

IMPLEMENTATION COMMIT — full working logic.

NOTE: This file assumes SensorNode (ABC) exists in src/sensors.py with the
constructor signature:
    __init__(self, sensor_id, location, unit, safe_min, safe_max,
              calibration_offset=0.0)
and SensorReading exists in src/readings.py with:
    __init__(self, sensor_id, value, unit, timestamp)

Once Emans and Ilukoyenikan push their files, replace the stub imports
below with the real ones and delete this file's standalone stub section.
"""

import random
import re
from datetime import datetime

# --- STUB SECTION: remove once teammates' real modules are merged ---
from abc import ABC, abstractmethod


class SensorReading:
    """Stub of the shared SensorReading value object for local testing."""

    def __init__(self, sensor_id, value, unit, timestamp):
        self.sensor_id = sensor_id
        self.value = value
        self.unit = unit
        self.timestamp = timestamp

    def __repr__(self):
        return (f"SensorReading(sensor_id={self.sensor_id!r}, "
                f"value={self.value!r}, unit={self.unit!r}, "
                f"timestamp={self.timestamp!r})")


class CalibrationError(IOError):
    """Stub of the shared CalibrationError for local testing."""

    def __init__(self, sensor_id: str, detail: str):
        super().__init__(f"[{sensor_id}] Calibration error: {detail}")
        self.sensor_id = sensor_id
        self.detail = detail
        self.timestamp = datetime.now()


class SensorNode(ABC):
    """Minimal stub of the shared SensorNode ABC for local testing."""

    _ID_PATTERN = re.compile(r"^SN-[A-Z]{4}-\d{2}$")

    def __init__(self, sensor_id, location, unit, safe_min, safe_max,
                 calibration_offset=0.0):
        if not self._ID_PATTERN.match(sensor_id):
            raise ValueError(
                f"Invalid sensor_id '{sensor_id}': must match "
                f"pattern SN-TTTT-NN"
            )
        self._sensor_id = sensor_id
        self.location = location
        self.unit = unit
        self.safe_min = safe_min
        self.safe_max = safe_max
        self._calibration_offset = 0.0
        self.calibrate(calibration_offset)

    @property
    @abstractmethod
    def sensor_id(self):
        """Abstract sensor_id property, implemented by subclasses."""
        raise NotImplementedError

    @property
    def calibration_offset(self):
        """Validated calibration offset, within +/-10% of full scale."""
        return self._calibration_offset

    @calibration_offset.setter
    def calibration_offset(self, value):
        full_scale = self.safe_max - self.safe_min
        limit = 0.10 * full_scale
        if abs(value) > limit:
            raise CalibrationError(
                getattr(self, "_sensor_id", "UNKNOWN"),
                f"offset {value} exceeds +/-{limit} allowed range"
            )
        self._calibration_offset = value

    @abstractmethod
    def read(self):
        """Abstract read method, implemented by subclasses."""
        raise NotImplementedError

    def calibrate(self, offset: float):
        """Set calibration_offset via the validated property."""
        self.calibration_offset = offset

    def self_test(self) -> bool:
        """Basic internal consistency check."""
        full_scale = self.safe_max - self.safe_min
        limit = 0.10 * full_scale
        return abs(self._calibration_offset) <= limit


# --- END STUB SECTION ---


class TemperatureNode(SensorNode):
    """
    Concrete SensorNode implementation for an industrial temperature sensor.

    Simulates a wireless or wired temperature probe reporting readings in
    degrees Celsius over one of the supported communication protocols
    (MQTT, Modbus, CAN Bus). Operates within a safe range of -40 to 150 C
    and flags an alarm condition above ALARM_THRESHOLD, though the actual
    alerting decision is delegated to AggregationHub via AlertRule.

    Class Attributes:
        ALARM_THRESHOLD (float): Temperature in Celsius above which a
            reading is considered alarm-worthy. Documented here for
            AlertRule configuration; this class does not raise on
            breach itself.

    Attributes:
        sensor_id (str): Unique identifier matching pattern SN-TEMP-NN.
        location (str): Physical installation location of the sensor.
        unit (str): Measurement unit, always "C" for this class.
        safe_min (float): Minimum safe operating temperature (-40.0).
        safe_max (float): Maximum safe operating temperature (150.0).
        calibration_offset (float): Per-sensor calibration adjustment.
    """

    ALARM_THRESHOLD = 120.0
    _SAFE_MIN = -40.0
    _SAFE_MAX = 150.0
    _UNIT = "\u00b0C"

    def __init__(self, sensor_id: str, location: str,
                 calibration_offset: float = 0.0):
        """
        Initialize a TemperatureNode.

        Args:
            sensor_id: Unique sensor identifier, pattern SN-TEMP-NN.
            location: Physical installation location string.
            calibration_offset: Initial calibration adjustment in Celsius.

        Raises:
            ValueError: If sensor_id does not match the SN-TEMP-NN pattern.
            CalibrationError: If calibration_offset exceeds the allowed
                +/-10% of full scale.
        """
        self._sensor_id_value = sensor_id
        super().__init__(
            sensor_id=sensor_id,
            location=location,
            unit=self._UNIT,
            safe_min=self._SAFE_MIN,
            safe_max=self._SAFE_MAX,
            calibration_offset=calibration_offset,
        )

    @property
    def sensor_id(self) -> str:
        """Return this sensor's unique identifier."""
        return self._sensor_id_value

    def read(self) -> SensorReading:
        """
        Take a simulated temperature reading.

        Generates a raw value that is mostly within the safe operating
        range, with a low-probability chance of spiking above
        ALARM_THRESHOLD so that alert-handling logic downstream
        (AlertRule / AggregationHub) has realistic data to react to.
        Applies calibration_offset before returning the result.

        Returns:
            SensorReading: A new reading with calibration_offset applied
            and timestamp set to the current time.
        """
        if random.random() < 0.08:
            raw_value = random.uniform(self.ALARM_THRESHOLD, self.safe_max)
        else:
            raw_value = random.uniform(self.safe_min, self.ALARM_THRESHOLD)

        calibrated_value = raw_value + self.calibration_offset

        return SensorReading(
            sensor_id=self.sensor_id,
            value=calibrated_value,
            unit=self.unit,
            timestamp=datetime.now(),
        )

    def __str__(self) -> str:
        """Return a human-readable description of this sensor."""
        return (f"TemperatureNode[{self.sensor_id}] at {self.location} "
                f"(range {self.safe_min} to {self.safe_max}{self._UNIT})")

    def __repr__(self) -> str:
        """Return an unambiguous developer-facing representation."""
        return (f"TemperatureNode(sensor_id={self.sensor_id!r}, "
                f"location={self.location!r}, "
                f"calibration_offset={self.calibration_offset!r})")
