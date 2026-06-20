"""Tests for MQTTProtocol (src/protocols.py).

random.random() is monkeypatched in the relevant tests so the low-probability
simulated connect failure never causes flaky results.
"""
from unittest.mock import patch

import pytest

from src.exceptions import CommunicationTimeoutError
from src.protocols import MQTTProtocol


def _connected_client() -> MQTTProtocol:
    """Return an MQTTProtocol guaranteed to connect successfully."""
    client = MQTTProtocol(broker_host="test-broker", port=1883, client_id="test-client")
    with patch("src.protocols.random.random", return_value=1.0):
        client.connect()
    return client


class TestMQTTProtocol:
    """Tests covering connect/send/receive/disconnect behaviour."""

    def test_connect_then_send_succeeds(self):
        """After a successful connect(), send() should return True."""
        client = _connected_client()
        assert client.is_connected is True
        assert client.send(b"hello") is True

    def test_send_without_connecting_raises(self):
        """send() before connect() must raise CommunicationTimeoutError."""
        client = MQTTProtocol(client_id="never-connected")
        with pytest.raises(CommunicationTimeoutError):
            client.send(b"hello")

    def test_receive_without_connecting_raises(self):
        """receive() before connect() must raise CommunicationTimeoutError."""
        client = MQTTProtocol(client_id="never-connected")
        with pytest.raises(CommunicationTimeoutError):
            client.receive(10)

    def test_receive_respects_max_bytes(self):
        """receive() must never return more than max_bytes bytes."""
        client = _connected_client()
        payload = client.receive(5)
        assert isinstance(payload, bytes)
        assert len(payload) <= 5

    def test_disconnect_resets_state(self):
        """disconnect() should set is_connected back to False."""
        client = _connected_client()
        assert client.is_connected is True
        client.disconnect()
        assert client.is_connected is False
        with pytest.raises(CommunicationTimeoutError):
            client.send(b"hello")

    def test_connect_can_simulate_timeout(self):
        """connect() raises CommunicationTimeoutError when failure is forced."""
        client = MQTTProtocol(client_id="flaky-client")
        with patch("src.protocols.random.random", return_value=0.0):
            with pytest.raises(CommunicationTimeoutError):
                client.connect()
        assert client.is_connected is False

    def test_default_client_id_is_generated(self):
        """If no client_id is given, one should be auto-generated and non-empty."""
        client = MQTTProtocol()
        assert isinstance(client.client_id, str)
        assert len(client.client_id) > 0

    def test_repr_and_str_contain_client_id(self):
        """__repr__ and __str__ should be informative and include the client_id."""
        client = MQTTProtocol(client_id="abc-123")
        assert "abc-123" in str(client)
        assert "abc-123" in repr(client)
