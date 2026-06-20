"""Tests for BatteryPoweredMixin + WirelessSensorNode (cooperative MI)."""

import pytest

from src.sensors import WirelessSensorNode, SensorNode, BatteryPoweredMixin
from src.readings import SensorReading


def node(**kwargs):
    return WirelessSensorNode("SN-WTMP-01", "Remote", "°C", -40.0, 150.0, **kwargs)


def test_battery_level_validation():
    with pytest.raises(ValueError):
        node(battery_level=-0.1)
    with pytest.raises(ValueError):
        node(battery_level=100.1)
    assert node(battery_level=0).battery_level == 0
    assert node(battery_level=100).battery_level == 100


def test_is_low_battery_boundary():
    assert node(battery_level=19.9).is_low_battery is True
    assert node(battery_level=20.1).is_low_battery is False


def test_read_drains_the_battery():
    n = node(battery_level=50.0, discharge_per_reading=1.0)
    n.read()
    assert n.battery_level == 49.0


def test_read_eventually_queues_a_low_alert():
    n = node(battery_level=20.4, discharge_per_reading=0.5)
    for _ in range(5):
        n.read()
    assert any(a.severity == "LOW" for a in n.pending_alerts)


def test_mro_includes_both_parents():
    mro = WirelessSensorNode.__mro__
    assert SensorNode in mro
    assert BatteryPoweredMixin in mro


def test_read_returns_a_reading():
    assert isinstance(node().read(), SensorReading)
