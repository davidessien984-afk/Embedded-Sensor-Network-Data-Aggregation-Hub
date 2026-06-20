"""Tests for ModbusProtocol."""

import pytest

from src.protocols import ModbusProtocol
from src.exceptions import CommunicationTimeoutError


def connected():
    dev = ModbusProtocol(device_address=3, baud_rate=19200)
    for _ in range(50):
        try:
            dev.connect()
            return dev
        except CommunicationTimeoutError:
            pass
    pytest.fail("Modbus never connected")


def test_connect_then_send():
    dev = connected()
    assert dev.is_connected is True
    assert dev.send(b"\x01\x03") is True


def test_send_without_connecting_raises():
    with pytest.raises(CommunicationTimeoutError):
        ModbusProtocol().send(b"\x01")


def test_receive_within_max_bytes():
    dev = connected()
    payload = dev.receive(4)
    assert isinstance(payload, bytes)
    assert len(payload) <= 4


def test_defaults():
    dev = ModbusProtocol()
    assert dev.device_address == 1
    assert dev.baud_rate == 9600
