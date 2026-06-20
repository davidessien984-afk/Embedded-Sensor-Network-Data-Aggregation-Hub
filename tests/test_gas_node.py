"""Tests for GasConcentrationNode."""

import pytest

from src.sensors import GasConcentrationNode
from src.readings import SensorReading


def test_unit_and_range():
    node = GasConcentrationNode("SN-GASC-04", "Vent")
    assert node.unit == "% LEL"
    assert node.safe_min == 0.0 and node.safe_max == 100.0


def test_alarm_threshold():
    assert GasConcentrationNode.ALARM_THRESHOLD == 20.0


def test_read_stays_in_range():
    node = GasConcentrationNode("SN-GASC-05", "Duct")
    for _ in range(50):
        r = node.read()
        assert isinstance(r, SensorReading)
        assert r.unit == "% LEL"
        assert 0.0 <= r.value <= 100.0


def test_bad_id_raises():
    with pytest.raises(ValueError):
        GasConcentrationNode("XX-GASC-04", "nowhere")  # wrong prefix
