"""Simulated communication protocols (MQTT, Modbus, CAN Bus).

None of these touch a real socket - they just model the connect/send/receive/
disconnect lifecycle so the rest of the system has something polymorphic to
talk to. The shared connect/guard logic lives on the base class; each subclass
fills in the abstract methods and its own constructor parameters.
"""

import random
from abc import ABC, abstractmethod

from src.exceptions import CommunicationTimeoutError


class CommunicationProtocol(ABC):
    """Abstract link layer. Subclasses simulate one real-world protocol each."""

    # chance a connect() attempt randomly "times out", for realism
    _CONNECT_FAILURE_PROBABILITY = 0.05

    def __init__(self) -> None:
        self._is_connected = False

    @abstractmethod
    def connect(self) -> bool:
        """Open the (simulated) connection. Returns True on success."""

    @abstractmethod
    def send(self, data: bytes) -> bool:
        """Send some bytes. Returns True on success."""

    @abstractmethod
    def receive(self, max_bytes: int) -> bytes:
        """Read up to max_bytes back."""

    @abstractmethod
    def disconnect(self) -> None:
        """Drop the connection."""

    @property
    def is_connected(self) -> bool:
        """Whether we currently think we're connected."""
        return self._is_connected

    # --- shared helpers the subclasses lean on -------------------------------

    def _open(self, who: str) -> bool:
        if random.random() < self._CONNECT_FAILURE_PROBABILITY:
            raise CommunicationTimeoutError(who, "connection attempt timed out")
        self._is_connected = True
        return True

    def _require_connected(self, who: str, op: str) -> None:
        if not self._is_connected:
            raise CommunicationTimeoutError(who, f"{op}() called while disconnected")


class MQTTProtocol(CommunicationProtocol):
    """A pretend MQTT publisher/subscriber."""

    def __init__(self, broker_host: str = "localhost", port: int = 1883,
                 client_id: str = "") -> None:
        super().__init__()
        self.broker_host = broker_host
        self.port = port
        self.client_id = client_id or f"mqtt-{random.randint(1000, 9999)}"

    def connect(self) -> bool:
        return self._open(self.client_id)

    def send(self, data: bytes) -> bool:
        self._require_connected(self.client_id, "send")
        return True

    def receive(self, max_bytes: int) -> bytes:
        self._require_connected(self.client_id, "receive")
        return b"mqtt-payload"[:max_bytes]

    def disconnect(self) -> None:
        self._is_connected = False

    def __str__(self) -> str:
        state = "connected" if self.is_connected else "disconnected"
        return f"MQTTProtocol({self.client_id} -> {self.broker_host}:{self.port}, {state})"

    def __repr__(self) -> str:
        return (f"MQTTProtocol(broker_host={self.broker_host!r}, port={self.port!r}, "
                f"client_id={self.client_id!r})")


class ModbusProtocol(CommunicationProtocol):
    """A pretend Modbus RTU master."""

    def __init__(self, device_address: int = 1, baud_rate: int = 9600) -> None:
        super().__init__()
        self.device_address = device_address
        self.baud_rate = baud_rate

    def _who(self) -> str:
        return f"modbus-{self.device_address}"

    def connect(self) -> bool:
        return self._open(self._who())

    def send(self, data: bytes) -> bool:
        self._require_connected(self._who(), "send")
        return True

    def receive(self, max_bytes: int) -> bytes:
        self._require_connected(self._who(), "receive")
        return b"modbus-frame"[:max_bytes]

    def disconnect(self) -> None:
        self._is_connected = False

    def __str__(self) -> str:
        state = "connected" if self.is_connected else "disconnected"
        return f"ModbusProtocol(addr={self.device_address} @ {self.baud_rate} baud, {state})"

    def __repr__(self) -> str:
        return (f"ModbusProtocol(device_address={self.device_address!r}, "
                f"baud_rate={self.baud_rate!r})")


class CANBusProtocol(CommunicationProtocol):
    """A pretend CAN bus node."""

    def __init__(self, bus_channel: str = "can0", bitrate: int = 500000) -> None:
        super().__init__()
        self.bus_channel = bus_channel
        self.bitrate = bitrate

    def connect(self) -> bool:
        return self._open(self.bus_channel)

    def send(self, data: bytes) -> bool:
        self._require_connected(self.bus_channel, "send")
        return True

    def receive(self, max_bytes: int) -> bytes:
        self._require_connected(self.bus_channel, "receive")
        return b"can-frame"[:max_bytes]

    def disconnect(self) -> None:
        self._is_connected = False

    def __str__(self) -> str:
        state = "connected" if self.is_connected else "disconnected"
        return f"CANBusProtocol({self.bus_channel} @ {self.bitrate} bps, {state})"

    def __repr__(self) -> str:
        return f"CANBusProtocol(bus_channel={self.bus_channel!r}, bitrate={self.bitrate!r})"
