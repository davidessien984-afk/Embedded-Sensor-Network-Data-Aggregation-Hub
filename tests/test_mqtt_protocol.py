"""Tests for MQTTProtocol (connect has a small random failure chance)."""

import pytest

from src.protocols import MQTTProtocol
from src.exceptions import CommunicationTimeoutError


def connected():
    client = MQTTProtocol(client_id="test-client")
    for _ in range(50):
        try:
            client.connect()
            return client
        except CommunicationTimeoutError:
            pass
    pytest.fail("MQTT never connected")


def test_connect_then_send():
    client = connected()
    assert client.is_connected is True
    assert client.send(b"hello") is True


def test_send_without_connecting_raises():
    with pytest.raises(CommunicationTimeoutError):
        MQTTProtocol().send(b"hello")


def test_disconnect_resets_state():
    client = connected()
    client.disconnect()
    assert client.is_connected is False
    with pytest.raises(CommunicationTimeoutError):
        client.receive(8)


def test_defaults():
    client = MQTTProtocol()
    assert client.broker_host == "localhost"
    assert client.port == 1883
    assert client.client_id  # auto-generated, non-empty
