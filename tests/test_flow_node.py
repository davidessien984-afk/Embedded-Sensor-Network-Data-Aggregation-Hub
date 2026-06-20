"""Tests for FlowRateNode."""

from datetime import datetime
from unittest.mock import patch

import pytest

from src.sensors import FlowRateNode
from src.readings import SensorReading
from src.exceptions import CalibrationError

OFFSET_LIMIT = 0.1 * (500.0 - 0.0)  # 50.0


def test_unit_range_and_threshold():
    node = FlowRateNode("SN-FLOW-05", "Header")
    assert node.unit == "L/min"
    assert node.safe_min == 0.0 and node.safe_max == 500.0
    assert FlowRateNode.ALARM_THRESHOLD == 450.0


@pytest.mark.parametrize("bad_id", ["SN-FLOW-1", "SN-FLO-01", "SNFLOW01", "SN-flow-01", ""])
def test_bad_ids_raise(bad_id):
    with pytest.raises(ValueError):
        FlowRateNode(bad_id, "nowhere")


def test_read_returns_reading_in_range():
    node = FlowRateNode("SN-FLOW-06", "Discharge", calibration_offset=5.0)
    for _ in range(100):
        r = node.read()
        assert isinstance(r, SensorReading)
        assert r.unit == "L/min"
        assert 0.0 <= r.value <= 500.0
        assert isinstance(r.timestamp, datetime)


def test_spike_branch_is_still_clamped():
    node = FlowRateNode("SN-FLOW-07", "Overflow")
    with patch("random.random", return_value=0.0), patch("random.uniform", return_value=480.0):
        r = node.read()
    assert 0.0 <= r.value <= 500.0


def test_offset_limits():
    node = FlowRateNode("SN-FLOW-08", "Manifold")
    node.calibrate(OFFSET_LIMIT)
    assert node.calibration_offset == OFFSET_LIMIT
    node.calibrate(-OFFSET_LIMIT)
    assert node.calibration_offset == -OFFSET_LIMIT
    with pytest.raises(CalibrationError):
        node.calibrate(OFFSET_LIMIT + 0.01)


def test_repr_and_str():
    node = FlowRateNode("SN-FLOW-09", "Lab Bench")
    assert "SN-FLOW-09" in str(node)
    assert "FlowRateNode" in repr(node)
