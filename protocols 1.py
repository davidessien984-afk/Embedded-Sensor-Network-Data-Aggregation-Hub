"""STUB for local testing only — the real CommunicationProtocol ABC is owned by
Falaiye Tobiloba Kayode. Replace this with their file when merging branches.
This stub mirrors the documented interface exactly so MQTTProtocol can be
developed and tested in isolation.
"""
from abc import ABC, abstractmethod


class CommunicationProtocol(ABC):
    """Abstract base class modelling a simulated communication protocol layer.

    No real sockets or networking are used anywhere in this project; all
    subclasses simulate connection, send, and receive behaviour in-memory.
    """

    def __init__(self) -> None:
        self._is_connected: bool = False

    @abstractmethod
    def connect(self) -> bool:
        """Establish a simulated connection. Returns True on success."""
        raise NotImplementedError

    @abstractmethod
    def send(self, data: bytes) -> bool:
        """Send data over the simulated link. Returns True on success."""
        raise NotImplementedError

    @abstractmethod
    def receive(self, max_bytes: int) -> bytes:
        """Receive up to max_bytes from the simulated link."""
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        """Tear down the simulated connection."""
        raise NotImplementedError

    @property
    def is_connected(self) -> bool:
        """bool: Whether the protocol currently reports an active connection."""
        return self._is_connected


import random

from src.exceptions import CommunicationTimeoutError


class MQTTProtocol(CommunicationProtocol):
    """A simulated MQTT client.

    This class models the basic lifecycle of an MQTT publisher/subscriber
    (connect, publish/send, receive, disconnect) without opening any real
    network sockets or depending on an external MQTT library. It is intended
    purely to demonstrate polymorphism alongside ModbusProtocol and
    CANBusProtocol under the shared CommunicationProtocol interface.

    Attributes:
        broker_host (str): Hostname of the simulated MQTT broker.
        port (int): Port of the simulated MQTT broker.
        client_id (str): Identifier this simulated client publishes under.
    """

    #: Probability (0.0-1.0) that a connect() attempt simulates a failure.
    _CONNECT_FAILURE_PROBABILITY = 0.05

    def __init__(self, broker_host: str = "localhost", port: int = 1883,
                 client_id: str = ""):
        """Initialize a simulated MQTT client.

        Args:
            broker_host: Hostname of the simulated broker.
            port: Port of the simulated broker.
            client_id: Identifier for this client. If empty, an id is
                generated automatically.
        """
        super().__init__()
        self.broker_host = broker_host
        self.port = port
        self.client_id = client_id or f"mqtt-client-{random.randint(1000, 9999)}"

    def connect(self) -> bool:
        """Simulate connecting to the MQTT broker.

        Returns:
            bool: True if the simulated connection succeeded.

        Raises:
            CommunicationTimeoutError: Raised with low probability to
                simulate a broker that is unreachable or slow to respond.
        """
        if random.random() < self._CONNECT_FAILURE_PROBABILITY:
            raise CommunicationTimeoutError(
                self.client_id,
                f"Timed out connecting to broker {self.broker_host}:{self.port}",
            )
        self._is_connected = True
        return True

    def send(self, data: bytes) -> bool:
        """Simulate publishing a message to the broker.

        Args:
            data: The payload to publish.

        Returns:
            bool: True if the simulated publish succeeded.

        Raises:
            CommunicationTimeoutError: If called while not connected.
        """
        if not self.is_connected:
            raise CommunicationTimeoutError(
                self.client_id, "send() called while not connected"
            )
        return True

    def receive(self, max_bytes: int) -> bytes:
        """Simulate receiving a subscribed message from the broker.

        Args:
            max_bytes: Maximum number of bytes to return.

        Returns:
            bytes: A simulated payload, truncated to max_bytes.

        Raises:
            CommunicationTimeoutError: If called while not connected.
        """
        if not self.is_connected:
            raise CommunicationTimeoutError(
                self.client_id, "receive() called while not connected"
            )
        simulated_payload = b"mqtt-simulated-payload"
        return simulated_payload[:max_bytes]

    def disconnect(self) -> None:
        """Simulate disconnecting from the broker."""
        self._is_connected = False

    def __str__(self) -> str:
        status = "connected" if self.is_connected else "disconnected"
        return f"MQTTProtocol({self.client_id} @ {self.broker_host}:{self.port}, {status})"

    def __repr__(self) -> str:
        return (
            f"MQTTProtocol(broker_host={self.broker_host!r}, port={self.port!r}, "
            f"client_id={self.client_id!r}, is_connected={self.is_connected!r})"
        )
