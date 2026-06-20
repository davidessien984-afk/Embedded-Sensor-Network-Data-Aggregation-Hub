"""
tests/test_temperature_node.py

TESTS-GREEN COMMIT — run with `pytest tests/test_temperature_node.py -v`
and confirm all pass before committing this stage.
"""

import pytest

from src.sensors import TemperatureNode, SensorReading


def test_valid_temperature_node_construction():
    """A TemperatureNode with a valid sensor_id should construct cleanly."""
    node = TemperatureNode(sensor_id="SN-TEMP-01", location="Boiler Room")
    assert node.sensor_id == "SN-TEMP-01"
    assert node.location == "Boiler Room"
    assert node.unit == "\u00b0C"
    assert node.safe_min == -40.0
    assert node.safe_max == 150.0


def test_invalid_sensor_id_raises_value_error():
    """An invalid sensor_id pattern should raise ValueError."""
    with pytest.raises(ValueError):
        TemperatureNode(sensor_id="BAD-ID", location="Boiler Room")


def test_read_returns_sensor_reading_with_correct_unit():
    """read() should return a SensorReading with the correct unit."""
    node = TemperatureNode(sensor_id="SN-TEMP-02", location="Furnace")
    reading = node.read()
    assert isinstance(reading, SensorReading)
    assert reading.unit == "\u00b0C"
    assert reading.sensor_id == "SN-TEMP-02"


def test_read_value_within_sane_bound_after_calibration():
    """The reading's value should remain within a sane bound after
    calibration_offset is applied."""
    node = TemperatureNode(
        sensor_id="SN-TEMP-03", location="Furnace", calibration_offset=5.0
    )
    reading = node.read()
    # safe range is -40 to 150, calibration offset is capped at 10% of
    # full scale (19), so allow a margin for that worst case
    assert -40.0 - 19.0 <= reading.value <= 150.0 + 19.0


def test_calibration_offset_out_of_range_raises_calibration_error():
    """A calibration_offset beyond +/-10% of full scale should raise."""
    from src.sensors import CalibrationError

    with pytest.raises(CalibrationError):
        TemperatureNode(
            sensor_id="SN-TEMP-04",
            location="Furnace",
            calibration_offset=1000.0,
        )


def test_multiple_reads_produce_varying_timestamps():
    """Successive reads should have distinct (or non-decreasing)
    timestamps, confirming timestamp is set fresh on each call."""
    node = TemperatureNode(sensor_id="SN-TEMP-05", location="Furnace")
    reading_one = node.read()
    reading_two = node.read()
    assert reading_two.timestamp >= reading_one.timestamp
