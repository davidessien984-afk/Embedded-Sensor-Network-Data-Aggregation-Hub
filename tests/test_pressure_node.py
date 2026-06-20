"""Tests for PressureNode."""

import pytest

from src.sensors import PressureNode
from src.readings import SensorReading


def test_unit_and_range():
    node = PressureNode("SN-PRES-02", "Line A")
    assert node.unit == "bar"
    assert node.safe_min == 0.0 and node.safe_max == 10.0


def test_alarm_threshold():
    assert PressureNode.ALARM_THRESHOLD == 9.0


def test_read_stays_in_range():
    node = PressureNode("SN-PRES-03", "Line B")
    for _ in range(50):
        r = node.read()
        assert isinstance(r, SensorReading)
        assert r.unit == "bar"
        assert 0.0 <= r.value <= 10.0


def test_bad_id_raises():
    with pytest.raises(ValueError):
        PressureNode("SN-PRESS-02", "nowhere")  # 5-letter type code
