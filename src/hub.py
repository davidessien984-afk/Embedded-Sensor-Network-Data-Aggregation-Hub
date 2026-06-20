"""The AggregationHub - where everything comes together.

The hub owns its sensors (composition: register one and the hub holds it for
good), runs every alert rule against every reading on each poll, sweeps up the
battery alerts that wireless nodes leave behind, and can spit out a JSON-ready
summary of what it's seen.
"""

import statistics
from collections import defaultdict


class AggregationHub:
    """Central registry + poller for a network of sensors."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._sensors = {}                  # sensor_id -> SensorNode (owned)
        self._rules = []                    # list[AlertRule]
        self._readings = defaultdict(list)  # sensor_id -> [SensorReading]
        self._alerts = []                   # every Alert raised so far

    def register(self, sensor) -> None:
        """Add a sensor. Two sensors can't share an id."""
        if sensor.sensor_id in self._sensors:
            raise ValueError(f"{sensor.sensor_id} is already registered")
        self._sensors[sensor.sensor_id] = sensor

    def add_alert_rule(self, rule) -> None:
        """Register a threshold rule the hub should apply on every poll."""
        self._rules.append(rule)

    def poll_all(self, timestamp=None):
        """Read every sensor once, run the rules, collect any alerts.

        Pass a timestamp to stamp this whole sweep with one time (handy when
        replaying a simulated 24-hour run); otherwise each reading keeps its
        own. Returns the list of readings taken.
        """
        collected = []
        for sensor in self._sensors.values():
            reading = sensor.read()
            if timestamp is not None:
                reading.timestamp = timestamp
            self._readings[reading.sensor_id].append(reading)
            collected.append(reading)

            for rule in self._rules:
                alert = rule.check(reading)
                if alert is not None:
                    self._alerts.append(alert)

            # wireless nodes stash low-battery alerts; take them and reset
            pending = getattr(sensor, "pending_alerts", None)
            if pending:
                self._alerts.extend(pending)
                pending.clear()
        return collected

    def get_alerts(self, severity: str = None):
        """All alerts (optionally just one severity), oldest first."""
        alerts = self._alerts
        if severity is not None:
            alerts = [a for a in alerts if a.severity == severity]
        return sorted(alerts, key=lambda a: a.timestamp)

    def _alert_counts(self, sensor_id):
        counts = {}
        for alert in self._alerts:
            if alert.sensor_id == sensor_id:
                counts[alert.severity] = counts.get(alert.severity, 0) + 1
        return counts

    def summary(self) -> dict:
        """Per-sensor stats as a plain dict you could json.dumps() straight off."""
        out = {}
        for sensor_id, readings in self._readings.items():
            values = [r.value for r in readings]
            out[sensor_id] = {
                "count": len(values),
                "mean": round(statistics.mean(values), 3),
                "min": round(min(values), 3),
                "max": round(max(values), 3),
                "std_dev": round(statistics.stdev(values), 3) if len(values) > 1 else 0.0,
                "alert_counts": self._alert_counts(sensor_id),
            }
        return out

    def __len__(self) -> int:
        return len(self._sensors)

    def __contains__(self, sensor_id) -> bool:
        return sensor_id in self._sensors

    def __iter__(self):
        return iter(self._sensors.values())

    def __str__(self) -> str:
        return f"AggregationHub({self.name!r}, {len(self)} sensors, {len(self._alerts)} alerts)"

    def __repr__(self) -> str:
        return f"AggregationHub(name={self.name!r})"
