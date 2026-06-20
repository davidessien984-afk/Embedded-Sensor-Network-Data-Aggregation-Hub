"""
tests/test_flow_node.py

Pytest tests for FlowRateNode in src/sensors.py.

Tests cover:
- Constructing a valid FlowRateNode
- Constructor rejects invalid sensor_id patterns (raises ValueError)
- read() returns a SensorReading with the correct unit
- read() value stays within the physical safe range after calibration
- calibration_offset boundary validation (exactly ±10% of full scale)
- calibrate() raises CalibrationError when offset is out of range
- __str__ and __repr__ produce non-empty strings
"""

import pytest
from datetime import datetime
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Minimal stubs so the test file is self-contained and can run before
# teammates' modules are merged.  Remove these stubs (and the sys.path block)
# once src/readings.py and src/exceptions.py exist in the repo.
# ---------------------------------------------------------------------------
import sys
import types

# ── stub: src.readings ──────────────────────────────────────────────────────
readings_mod = types.ModuleType("src.readings")


class _SensorReading:
    """Minimal SensorReading stub for isolated testing."""

    def __init__(self, sensor_id, value, unit, timestamp):
        self.sensor_id = sensor_id
        self.value = value
        self.unit = unit
        self.timestamp = timestamp


readings_mod.SensorReading = _SensorReading
sys.modules.setdefault("src", types.ModuleType("src"))
sys.modules["src.readings"] = readings_mod

# ── stub: src.exceptions ────────────────────────────────────────────────────
exceptions_mod = types.ModuleType("src.exceptions")


class _SensorOfflineError(IOError):
    def __init__(self, sensor_id, detail):
        super().__init__(f"[{sensor_id}] Offline: {detail}")
        self.sensor_id = sensor_id
        self.detail = detail
        self.timestamp = datetime.now()


class _CalibrationError(IOError):
    def __init__(self, sensor_id, detail):
        super().__init__(f"[{sensor_id}] Calibration: {detail}")
        self.sensor_id = sensor_id
        self.detail = detail
        self.timestamp = datetime.now()


class _CommunicationTimeoutError(IOError):
    def __init__(self, sensor_id, detail):
        super().__init__(f"[{sensor_id}] Timeout: {detail}")
        self.sensor_id = sensor_id
        self.detail = detail
        self.timestamp = datetime.now()


exceptions_mod.SensorOfflineError = _SensorOfflineError
exceptions_mod.CalibrationError = _CalibrationError
exceptions_mod.CommunicationTimeoutError = _CommunicationTimeoutError
sys.modules["src.exceptions"] = exceptions_mod

# ---------------------------------------------------------------------------
# Now import the real module under test
# ---------------------------------------------------------------------------
from src.sensors import FlowRateNode  # noqa: E402  (imports after stubs)
from src.readings import SensorReading  # noqa: E402
from src.exceptions import CalibrationError  # noqa: E402

# ---------------------------------------------------------------------------
# Constants mirrored from FlowRateNode for readability
# ---------------------------------------------------------------------------
SAFE_MIN = 0.0
SAFE_MAX = 500.0
FULL_SCALE = SAFE_MAX - SAFE_MIN          # 500.0
OFFSET_LIMIT = 0.1 * FULL_SCALE          # 50.0  (±10 % of full scale)


# ===========================================================================
# Test 1 — valid construction
# ===========================================================================
class TestFlowRateNodeConstruction:
    """Tests for valid and invalid FlowRateNode construction."""

    def test_valid_construction(self):
        """A correctly formatted sensor_id should not raise any exception."""
        node = FlowRateNode("SN-FLOW-01", "Pump Station A")
        assert node.sensor_id == "SN-FLOW-01"
        assert node.location == "Pump Station A"
        assert node.unit == "L/min"

    def test_valid_construction_with_offset(self):
        """Constructor should accept a calibration_offset within ±10% of full scale."""
        node = FlowRateNode("SN-FLOW-02", "Cooling Loop", calibration_offset=10.0)
        assert node.calibration_offset == 10.0

    def test_alarm_threshold_constant(self):
        """ALARM_THRESHOLD class constant must equal 450.0."""
        assert FlowRateNode.ALARM_THRESHOLD == 450.0


# ===========================================================================
# Test 2 — sensor_id validation
# ===========================================================================
class TestSensorIdValidation:
    """Sensor IDs that violate the SN-TTTT-NN pattern must raise ValueError."""

    @pytest.mark.parametrize("bad_id", [
        "SN-FLOW-1",        # only 1 digit
        "SN-FLO-01",        # only 3 letters in type code
        "SNFLOW01",         # missing hyphens
        "SN-flow-01",       # lowercase type code
        "",                 # empty string
        "SN-FLOW-001",      # 3 digits instead of 2
        "SN-FLOWW-01",      # 5 letters in type code
    ])
    def test_invalid_sensor_id_raises_value_error(self, bad_id):
        """Invalid sensor_id patterns must raise ValueError."""
        with pytest.raises(ValueError):
            FlowRateNode(bad_id, "Test Location")

    def test_valid_sensor_id_pattern(self):
        """Any two-digit suffix with a four-letter type code should be accepted."""
        node = FlowRateNode("SN-FLOW-99", "Far End")
        assert node.sensor_id == "SN-FLOW-99"


# ===========================================================================
# Test 3 — read() return type and unit
# ===========================================================================
class TestFlowRateNodeRead:
    """Tests for the read() method output."""

    def test_read_returns_sensor_reading(self):
        """read() must return a SensorReading instance."""
        node = FlowRateNode("SN-FLOW-03", "Main Header")
        reading = node.read()
        assert isinstance(reading, SensorReading)

    def test_read_unit_is_l_per_min(self):
        """The reading unit must be 'L/min'."""
        node = FlowRateNode("SN-FLOW-04", "Bypass Line")
        reading = node.read()
        assert reading.unit == "L/min"

    def test_read_sensor_id_matches_node(self):
        """The reading's sensor_id must match the node's sensor_id."""
        node = FlowRateNode("SN-FLOW-05", "Return Loop")
        reading = node.read()
        assert reading.sensor_id == "SN-FLOW-05"

    def test_read_value_within_safe_range(self):
        """
        After calibration is applied and clamping occurs, the reading value
        must stay within [0.0, 500.0] L/min over many calls.
        """
        node = FlowRateNode("SN-FLOW-06", "Discharge Header", calibration_offset=5.0)
        for _ in range(100):
            reading = node.read()
            assert SAFE_MIN <= reading.value <= SAFE_MAX, (
                f"Value {reading.value} is outside safe range [{SAFE_MIN}, {SAFE_MAX}]"
            )

    def test_read_has_timestamp(self):
        """The reading timestamp must be a datetime instance."""
        node = FlowRateNode("SN-FLOW-07", "Tank Outlet")
        reading = node.read()
        assert isinstance(reading.timestamp, datetime)

    def test_read_spike_path(self):
        """
        When the internal random draw always returns 0.0 (< spike probability),
        the raw value is drawn from the spike range (above ALARM_THRESHOLD).
        The clamped result must still be within [0, 500].
        """
        node = FlowRateNode("SN-FLOW-08", "Overflow Pipe")
        # Force spike branch: patch random.random to always return 0.0
        with patch("random.random", return_value=0.0):
            # patch random.uniform to return a spike value
            with patch("random.uniform", return_value=480.0):
                reading = node.read()
        assert SAFE_MIN <= reading.value <= SAFE_MAX


# ===========================================================================
# Test 4 — calibration_offset validation
# ===========================================================================
class TestCalibrationOffset:
    """Tests for calibration_offset property boundaries."""

    def test_offset_at_positive_limit_is_accepted(self):
        """Offset exactly at +10% of full scale (50.0) must be accepted."""
        node = FlowRateNode("SN-FLOW-09", "Inlet Manifold")
        node.calibrate(OFFSET_LIMIT)  # should not raise
        assert node.calibration_offset == OFFSET_LIMIT

    def test_offset_at_negative_limit_is_accepted(self):
        """Offset exactly at -10% of full scale (-50.0) must be accepted."""
        node = FlowRateNode("SN-FLOW-10", "Outlet Manifold")
        node.calibrate(-OFFSET_LIMIT)  # should not raise
        assert node.calibration_offset == -OFFSET_LIMIT

    def test_offset_just_above_limit_raises_calibration_error(self):
        """An offset just above +10% of full scale must raise CalibrationError."""
        node = FlowRateNode("SN-FLOW-11", "Bypass Valve")
        with pytest.raises(CalibrationError):
            node.calibrate(OFFSET_LIMIT + 0.01)

    def test_offset_just_below_negative_limit_raises_calibration_error(self):
        """An offset just below -10% of full scale must raise CalibrationError."""
        node = FlowRateNode("SN-FLOW-12", "Recirculation Loop")
        with pytest.raises(CalibrationError):
            node.calibrate(-(OFFSET_LIMIT + 0.01))

    def test_zero_offset_is_always_valid(self):
        """A calibration_offset of 0.0 must always be accepted."""
        node = FlowRateNode("SN-FLOW-13", "Test Stand")
        node.calibrate(0.0)
        assert node.calibration_offset == 0.0


# ===========================================================================
# Test 5 — string representations
# ===========================================================================
class TestStringRepresentations:
    """__str__ and __repr__ must return non-empty, descriptive strings."""

    def test_str_contains_sensor_id(self):
        node = FlowRateNode("SN-FLOW-14", "Lab Bench")
        assert "SN-FLOW-14" in str(node)

    def test_repr_contains_class_name(self):
        node = FlowRateNode("SN-FLOW-15", "Lab Bench")
        assert "FlowRateNode" in repr(node)

    def test_repr_contains_location(self):
        node = FlowRateNode("SN-FLOW-16", "Lab Bench")
        assert "Lab Bench" in repr(node)
