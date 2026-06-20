"""Custom exceptions for the hub.

These all subclass IOError, since each one is really an I/O failure against a
(simulated) device. Every exception carries the sensor id, a short detail
message and a timestamp, so logs and alerts can show what broke and when.
"""

from datetime import datetime


class SensorHubError(IOError):
    """Base class for every error the hub raises.

    One shared base lets callers catch everything with `except SensorHubError`
    or pick out the specific subclasses when they actually care which failed.
    """

    def __init__(self, sensor_id: str, detail: str, prefix: str = "Error") -> None:
        super().__init__(f"[{sensor_id}] {prefix}: {detail}")
        self.sensor_id = sensor_id
        self.detail = detail
        self.timestamp = datetime.now()

    def __repr__(self) -> str:
        return (f"{type(self).__name__}(sensor_id={self.sensor_id!r}, "
                f"detail={self.detail!r}, timestamp={self.timestamp!r})")


class SensorOfflineError(SensorHubError):
    """Sensor stopped responding or failed its self-test."""

    def __init__(self, sensor_id: str, detail: str) -> None:
        super().__init__(sensor_id, detail, prefix="Offline")


class CalibrationError(SensorHubError):
    """Calibration offset landed outside the allowed +/-10% of full scale."""

    def __init__(self, sensor_id: str, detail: str) -> None:
        super().__init__(sensor_id, detail, prefix="Calibration")


class CommunicationTimeoutError(SensorHubError):
    """A protocol connect/send/receive call timed out."""

    def __init__(self, sensor_id: str, detail: str) -> None:
        super().__init__(sensor_id, detail, prefix="Timeout")
