"""
src/sensors.py (TemperatureNode section)

SKELETON COMMIT — structure only, no implementation logic yet.
This file will be merged into the shared src/sensors.py once Emans
Gift Oghenemine's SensorNode ABC is finalized.
"""

from src.sensors import SensorNode
from src.readings import SensorReading


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
        raise NotImplementedError

    def read(self) -> SensorReading:
        """
        Take a simulated temperature reading.

        Returns:
            SensorReading: A new reading with calibration_offset applied
            and timestamp set to the current time.
        """
        raise NotImplementedError

    def __str__(self) -> str:
        """Return a human-readable description of this sensor."""
        raise NotImplementedError

    def __repr__(self) -> str:
        """Return an unambiguous developer-facing representation."""
        raise NotImplementedError
