"""Tests for TemperatureNode."""

import pytest

from src.sensors import TemperatureNode
from src.readings import SensorReading


def test_unit_and_range():
    node = TemperatureNode("SN-TEMP-01", "Boiler")
    assert node.unit == "°C"
    assert node.safe_min == -40.0 and node.safe_max == 150.0


def test_alarm_threshold():
    assert TemperatureNode.ALARM_THRESHOLD == 120.0


def test_read_stays_in_range():
    node = TemperatureNode("SN-TEMP-02", "Furnace")
    for _ in range(50):
        r = node.read()
        assert isinstance(r, SensorReading)
        assert r.unit == "°C"
        assert -40.0 <= r.value <= 150.0


def test_bad_id_raises():
    with pytest.raises(ValueError):
        TemperatureNode("TEMP-01", "nowhere")
