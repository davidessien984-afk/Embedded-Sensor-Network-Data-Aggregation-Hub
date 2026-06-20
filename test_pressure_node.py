"""Tests for PressureNode (src/sensors.py)."""

import pytest

from src.sensors import PressureNode
from src.readings import SensorReading


class TestPressureNodeConstruction:
    """Tests for PressureNode construction and validation."""

    def test_valid_construction(self):
        """A PressureNode with a valid sensor_id constructs successfully."""
        node = PressureNode(sensor_id="SN-PRES-02", location="Pump Room A")
        assert node.sensor_id == "SN-PRES-02"
        assert node.unit == "bar"
        assert node.safe_min == 0.0
        assert node.safe_max == 10.0

    def test_invalid_sensor_id_raises_value_error(self):
        """An invalid sensor_id pattern raises ValueError."""
        with pytest.raises(ValueError):
            PressureNode(sensor_id="BAD-ID", location="Pump Room A")


class TestPressureNodeRead:
    """Tests for PressureNode.read()."""

    def test_read_returns_sensor_reading_with_correct_unit(self):
        """read() returns a SensorReading instance with unit 'bar'."""
        node = PressureNode(sensor_id="SN-PRES-02", location="Pump Room A")
        reading = node.read()
        assert isinstance(reading, SensorReading)
        assert reading.unit == "bar"
        assert reading.sensor_id == "SN-PRES-02"

    def test_read_value_within_sane_bound_after_calibration(self):
        """The value returned by read() stays within a reasonable bound
        once the calibration offset is taken into account."""
        offset = 0.5
        node = PressureNode(
            sensor_id="SN-PRES-02",
            location="Pump Room A",
            calibration_offset=offset,
        )
        reading = node.read()
        assert -1.0 <= reading.value <= node.safe_max + 1.0 + offset

    def test_multiple_reads_eventually_produce_alarm_value(self):
        """Across many reads, at least one should exceed ALARM_THRESHOLD,
        confirming the alarm-spike simulation path is reachable."""
        node = PressureNode(sensor_id="SN-PRES-02", location="Pump Room A")
        readings = [node.read() for _ in range(200)]
        assert any(r.value > PressureNode.ALARM_THRESHOLD for r in readings)
      
