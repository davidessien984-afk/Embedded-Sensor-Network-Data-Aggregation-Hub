"""Tests for CANBusProtocol."""

import pytest

from src.protocols import CANBusProtocol
from src.exceptions import CommunicationTimeoutError


def connected():
    bus = CANBusProtocol(bus_channel="can0", bitrate=500000)
    for _ in range(50):
        try:
            bus.connect()
            return bus
        except CommunicationTimeoutError:
            pass
    pytest.fail("CAN bus never connected")


def test_connect_then_send():
    bus = connected()
    assert bus.is_connected is True
    assert bus.send(b"\x01\x02\x03") is True


def test_send_without_connecting_raises():
    with pytest.raises(CommunicationTimeoutError):
        CANBusProtocol().send(b"\x01")


def test_disconnect_then_send_raises():
    bus = connected()
    bus.disconnect()
    with pytest.raises(CommunicationTimeoutError):
        bus.send(b"\x01")


def test_receive_within_max_bytes():
    bus = connected()
    payload = bus.receive(4)
    assert isinstance(payload, bytes)
    assert len(payload) <= 4


def test_defaults_and_repr():
    bus = CANBusProtocol()
    assert bus.bus_channel == "can0"
    assert bus.bitrate == 500000
    assert "can0" in repr(bus) and "can0" in str(bus)
