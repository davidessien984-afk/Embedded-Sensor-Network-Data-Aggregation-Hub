"""Alerts and the rules that raise them.

An AlertRule watches one sensor and fires an Alert when a reading leaves its
[min, max] band. How badly it leaves the band decides the severity. Alerts
sort by severity so they can be dropped straight into a priority queue.
"""


class Alert:
    """Something went out of range and someone should know about it."""

    # higher number == more urgent; used by __lt__ for sorting
    SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

    def __init__(self, sensor_id, severity, message, timestamp):
        if severity not in self.SEVERITY_RANK:
            raise ValueError(
                f"severity must be one of {sorted(self.SEVERITY_RANK)}, got {severity!r}")
        self.sensor_id = sensor_id
        self.severity = severity
        self.message = message
        self.timestamp = timestamp

    @property
    def rank(self):
        """Numeric priority of this alert (CRITICAL is highest)."""
        return self.SEVERITY_RANK[self.severity]

    def __lt__(self, other):
        if not isinstance(other, Alert):
            return NotImplemented
        return self.rank < other.rank

    def __eq__(self, other):
        if not isinstance(other, Alert):
            return NotImplemented
        return (self.sensor_id, self.severity, self.message, self.timestamp) == \
               (other.sensor_id, other.severity, other.message, other.timestamp)

    def __str__(self):
        return f"[{self.severity}] {self.sensor_id}: {self.message}"

    def __repr__(self):
        return (f"Alert(sensor_id={self.sensor_id!r}, severity={self.severity!r}, "
                f"message={self.message!r}, timestamp={self.timestamp!r})")


class AlertRule:
    """A min/max band for one sensor. check() turns a breach into an Alert."""

    def __init__(self, sensor_id, min_threshold, max_threshold):
        if min_threshold > max_threshold:
            raise ValueError(
                f"min_threshold {min_threshold} can't be above max_threshold {max_threshold}")
        self.sensor_id = sensor_id
        self.min_threshold = float(min_threshold)
        self.max_threshold = float(max_threshold)

    def _severity_for(self, value):
        """Pick a severity from how far past the threshold we are.

        Within 10% over/under the broken threshold is MEDIUM, up to 25% is
        HIGH, beyond that is CRITICAL.
        """
        if value > self.max_threshold:
            ref = abs(self.max_threshold) or 1.0
            overshoot = (value - self.max_threshold) / ref
        else:
            ref = abs(self.min_threshold) or 1.0
            overshoot = (self.min_threshold - value) / ref

        if overshoot <= 0.10:
            return "MEDIUM"
        if overshoot <= 0.25:
            return "HIGH"
        return "CRITICAL"

    def check(self, reading):
        """Return an Alert if reading is out of band, else None.

        Readings from a different sensor (or ones still inside the band) just
        return None - the rule doesn't apply.
        """
        if reading.sensor_id != self.sensor_id:
            return None
        if self.min_threshold <= reading.value <= self.max_threshold:
            return None

        msg = (f"value {reading.value:.2f} {getattr(reading, 'unit', '')} "
               f"out of band [{self.min_threshold}, {self.max_threshold}]").strip()
        return Alert(reading.sensor_id, self._severity_for(reading.value),
                     msg, reading.timestamp)

    def __str__(self):
        return f"AlertRule({self.sensor_id}: [{self.min_threshold}, {self.max_threshold}])"

    def __repr__(self):
        return (f"AlertRule(sensor_id={self.sensor_id!r}, "
                f"min_threshold={self.min_threshold!r}, max_threshold={self.max_threshold!r})")
