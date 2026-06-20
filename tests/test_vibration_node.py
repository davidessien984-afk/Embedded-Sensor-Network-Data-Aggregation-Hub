"""Tests for VibrationNode."""

import pytest

from src.sensors import VibrationNode
from src.readings import SensorReading


def test_unit_and_range():
    node = VibrationNode("SN-VIBR-03", "Pump 1")
    assert node.unit == "mm/s"
    assert node.safe_min == 0.0 and node.safe_max == 25.0


def test_alarm_threshold():
    assert VibrationNode.ALARM_THRESHOLD == 20.0


def test_read_stays_in_range():
    node = VibrationNode("SN-VIBR-04", "Pump 2")
    for _ in range(50):
        r = node.read()
        assert isinstance(r, SensorReading)
        assert r.unit == "mm/s"
        assert 0.0 <= r.value <= 25.0


def test_bad_id_raises():
    with pytest.raises(ValueError):
        VibrationNode("SN-VIBR-3", "nowhere")  # one-digit suffix
