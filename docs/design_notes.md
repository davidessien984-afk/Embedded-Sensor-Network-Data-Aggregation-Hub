# Design Notes — Embedded Sensor Network Data Aggregation Hub

These notes explain *why* the code is shaped the way it is. The class diagram
in `../uml/class_diagram.puml` is the picture; this is the reasoning behind it.

## The two hierarchies

The system has two parallel abstractions, each an ABC with concrete children:

- **`SensorNode`** — what every sensor can do (`read`, `calibrate`,
  `self_test`). The five concrete nodes (temperature, pressure, vibration, gas,
  flow) differ only in three things: their unit, their safe range, and their
  alarm threshold. Because that's all that changes, the actual reading
  simulation lives *once* in `SensorNode._simulate_reading()` and each subclass
  just calls it. That keeps the nodes to a few lines each and means there is no
  copy-pasted `read()` body to drift out of sync.
- **`CommunicationProtocol`** — connect / send / receive / disconnect. MQTT,
  Modbus and CAN Bus each fill those in, but the shared "am I connected?" guard
  and the random-timeout logic sit on the base (`_open`, `_require_connected`)
  so the three stubs stay tiny and behave identically where they should.

Keeping the abstract methods genuinely abstract (via `abc.abstractmethod`) means
neither base can be instantiated by mistake — both are covered by a test that
asserts `TypeError`.

## Composition vs aggregation

This was the decision worth thinking about up front.

- **`AggregationHub` ◆— `SensorNode` is composition.** Once a sensor is
  `register()`-ed, the hub is the thing that drives it: it polls it, keeps its
  reading history, and decides when it's read. The sensor has no independent
  job in the running system outside the hub that owns it, so conceptually the
  hub *owns* its sensors — a filled-diamond composition.
- **`AggregationHub` ◇— `AlertRule` is aggregation.** Alert rules are plain
  configuration objects. They're built outside the hub and handed in with
  `add_alert_rule()`; the same rule could be inspected, reused or swapped
  without the hub creating or destroying it. The hub only holds a reference, so
  this is a hollow-diamond aggregation.

Drawing those two relationships differently is what stopped the hub from
turning into a god-object: rules stay dumb and testable on their own, and the
hub doesn't need to know how a rule decides severity.

## Cooperative multiple inheritance

`WirelessSensorNode(SensorNode, BatteryPoweredMixin)` is the one place we use
multiple inheritance, and it only works because of cooperative `super()` calls:

```
WirelessSensorNode -> SensorNode -> BatteryPoweredMixin -> object
```

`SensorNode.__init__` takes `**kwargs` and passes whatever it doesn't recognise
up the chain, so the `battery_level` / `discharge_per_reading` arguments flow
past it and land on the mixin. If `SensorNode` had hard-coded
`super().__init__()` with no kwargs, the mixin would never get its arguments —
this is exactly the trap cooperative MI avoids, and there's a test asserting
both parents appear in the MRO.

## Value object and operator overloading

`SensorReading` is a small immutable-by-convention value object. It leans on
`functools.total_ordering` so we only hand-write `__eq__` and `__lt__` and get
the other three comparisons for free. `__add__`/`__radd__` let readings be
summed (including with the built-in `sum()`), and `__abs__` is overloaded to
mean "deviation from setpoint", which reads naturally at the call site.

## Duck typing

`DataPipeline.process()` doesn't ask for a `SensorNode` — it asks for anything
that satisfies the `Readable` protocol (`typing.Protocol`, `@runtime_checkable`).
That's why the hub tests can feed it a throwaway class that just happens to have
a `read()` method. Structural typing here keeps the pipeline decoupled from the
sensor hierarchy entirely.

## What we deliberately left simple

See "Known Limitations" in the README — the protocols are in-memory stubs, the
sensor data is random rather than replayed from a real trace, and everything is
held in memory for the length of a run. Those were scoping choices, not
oversights; the brief explicitly says no GUI and no database are required.
