"""Tests for the CommunicationProtocol ABC and its shared is_connected logic."""

import pytest

from src.protocols import CommunicationProtocol


class DummyLink(CommunicationProtocol):
    """Bare concrete protocol, just enough to exercise the base class."""

    def connect(self):
        return self._open("dummy")

    def send(self, data):
        self._require_connected("dummy", "send")
        return True

    def receive(self, max_bytes):
        self._require_connected("dummy", "receive")
        return b"x"[:max_bytes]

    def disconnect(self):
        self._is_connected = False


def _connect(link, tries=50):
    for _ in range(tries):
        try:
            link.connect()
            return
        except Exception:
            pass
    pytest.fail("could not connect after several tries")


def test_abc_cannot_be_instantiated():
    with pytest.raises(TypeError):
        CommunicationProtocol()


def test_is_connected_tracks_state():
    link = DummyLink()
    assert link.is_connected is False
    _connect(link)
    assert link.is_connected is True
    link.disconnect()
    assert link.is_connected is False
