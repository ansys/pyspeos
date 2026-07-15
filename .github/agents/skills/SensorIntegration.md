# Skill: Implement and maintain sensors

Use this skill file when you need to add, modify, debug, or test any sensor workflow in PySpeos.

---

## Scope

This skill covers the standard sensor implementation pattern across:

- Parameter objects in `src/ansys/speos/core/generic/parameters.py`
- Feature classes in `src/ansys/speos/core/sensor.py`
- Factory creation and scene hydration in `src/ansys/speos/core/project.py`
- Unit and load tests in `tests/core/test_sensor.py`

For an end-to-end concrete example, see the `SensorPolarIntensity` section in this file.

---

## Sensor architecture pattern

Every sensor feature should follow the same flow:

1. Define a `@dataclass` for defaults and user-facing configuration.
2. Implement a `BaseSensor` subclass with typed properties and setters.
3. Apply defaults in `_fill_parameters()` for both:
   - new objects created from parameter dataclasses
   - hydrated objects loaded from existing scene protobuf messages
4. Register the sensor in `Project.create_sensor()`.
5. Register load-time mapping in `Project._fill_features()`.
6. Add tests that verify both creation and hydration behavior.

---

## Proto mapping matrix (recommended before coding)

Before implementation, create a mapping table in your PR notes.

| Python API | Proto field | Scope | Notes |
|---|---|---|---|
| `sensor.<prop>` | `<sensor>_sensor_template.<prop>` | Template | Shared/configuration state |
| `sensor.<instance_prop>` | `<sensor>_properties.<instance_prop>` | Instance | Placement/runtime state |
| `set_<group>()` | nested proto message | Template | Return helper class |
| `None` setter path | `ClearField("...")` | Template/Instance | Optional field disable path |

Observer reference mapping:

- `SensorObserver.focal` -> `observer_sensor_template.focal`
- `SensorObserver.axis_system` -> `observer_properties.axis_system`
- `SensorObserver.set_angular_range()` -> `observer_sensor_template.sensors_locations`
- `SensorObserver.stereo_interocular_distance = None` -> `observer_sensor_template.ClearField("stereo")`

This catches naming and scope mismatches early.

---

## Hydration contract (must hold for every sensor)

Creation and hydration must be deterministic:

- In `Project._fill_features()`, map each `HasField("<sensor>_properties")` to the matching sensor class.
- Constructor hydration path uses `sensor_instance=...` with `default_parameters=None`.
- `_fill_parameters()` must only apply defaults when `default_parameters` is provided.
- Hydration path must not overwrite values already loaded from scene protobuf.

Rule:

- `default_parameters is not None` => creation/default assignment path
- `default_parameters is None` => hydration/read-existing path

---

## Nested helper pattern (`stable_ctr` guard)

For nested configuration objects, use guarded helper classes (for example `BaseSensor.Dimensions`, `BaseSensor.AngularRange`).

- Helper class constructor accepts `stable_ctr: bool = False`.
- Raise `RuntimeError` when instantiated directly by users.
- Expose helper only through parent `set_<group>()` method with `stable_ctr=True`.

This keeps nested protobuf mutations controlled and consistent.

---

## Optional field semantics (enable/disable behavior)

For optional embedded protobuf messages:

- Assign value => set field content.
- Assign `None` => clear field via `ClearField("...")`.

Always test both transitions:

1. unset -> set
2. set -> clear (`None`)
3. clear state after `commit()` and hydration

---

## Required implementation checklist (all sensors)

1. Add or update parameter dataclasses in `generic/parameters.py`.
2. Implement or update sensor class logic in `sensor.py`.
3. Keep constructor parity with existing sensors (`project`, `name`, `description`, `metadata`, `sensor_instance`, `default_parameters`).
4. Ensure `_fill_parameters()` handles creation and hydration paths consistently.
5. Add or update dispatch and parameter type validation in `Project.create_sensor()`.
6. Add or update scene hydration dispatch in `Project._fill_features()`.
7. Add or update tests in `tests/core/test_sensor.py`:
   - default creation tests
   - parameterized creation tests
   - load/hydration verification tests
8. Add or update changelog fragment in `doc/changelog.d/`.
9. Run:
   - `ruff check --fix`
   - `ruff format`
10. Run focused syntax and pytest validation for the new sensor keyword.

---

## Cross-sensor behavior invariants

Keep these patterns stable unless an intentional API change is requested:

- `create_sensor()` must reject wrong parameter types with clear `TypeError` messages.
- `_fill_parameters()` must not diverge between fresh creation and loaded-scene hydration.
- Property getters/setters should map directly to protobuf fields with minimal hidden side effects.
- If a sensor uses `oneof` protobuf groups, setter logic should only mutate the targeted group.
- Property access that is invalid for the active mode should raise explicit errors.
- Scene instance properties (for example axis/frame fields) must be preserved across `commit()` and reload.

---

## Proto and oneof handling rules

When sensor templates rely on protobuf `oneof` groups:

- Use `SetInParent()` to activate empty oneof members when needed.
- Use `HasField()` before reading mode-dependent fields.
- Do not reset unrelated oneof groups while switching one mode.
- Add tests that assert active oneof members after each setter path.

This avoids subtle regressions in mode switching and hydration.

---

## Testing strategy (all sensors)

At minimum, verify:

- template exists and expected template subtype is active
- default values match dataclass defaults
- each key setter persists value after `commit()`
- oneof/mode switches select expected fields
- load-from-file hydration reconstructs expected state
- scene-instance properties (for example axis systems) persist

When adding load tests, mirror the assertions used by existing sensor load tests in `tests/core/test_sensor.py`.

### Minimal test blueprint for new sensors

At minimum, add tests for:

1. Factory creation with default dataclass.
2. Creation with custom dataclass values.
3. Property getter/setter round-trips.
4. Nested helper (`set_*`) round-trips.
5. `commit()` persistence (template type + values).
6. Scene hydration parity (loaded object values match committed values).
7. Optional `None` clear-paths (if applicable).

---

## Worked example: `SensorPolarIntensity`

`SensorPolarIntensity` is a complete reference implementation for mode-rich sensors.

It demonstrates:

- enum-backed format modes via `PolarIntensityFormatTypes`
- dual sampling representation (`PolarIntensityDimensionsParameters | str`)
- field-mode switching between far-field and near-field inputs
- guarded cross-mode property access with `TypeError`
- creation + hydration parity inside `_fill_parameters()`
- explicit project integration in both `create_sensor()` and `_fill_features()`

When implementing another sensor with similar mode complexity, copy this pattern first and then adapt names and field mappings.

---

## Common pitfalls

- Implementing only creation logic and forgetting hydration logic.
- Reading mode-dependent fields without `HasField()` guards.
- Accidentally overwriting unrelated oneof branches.
- Registering factory dispatch but missing `_fill_features()` hydration mapping.
- Updating feature code without updating both creation and load tests.
- Defining helper classes at the wrong nesting/indentation level in `sensor.py`.
- Writing defaults during hydration because `_fill_parameters()` does not guard `default_parameters is None`.
- Registering in `create_sensor()` but forgetting supported-list update in default `TypeError` branch.

---

## Validation commands (Windows / PowerShell)

Run these after implementation updates:

```powershell
cd D:\work\Gitdir\pyspeos
python -m py_compile src/ansys/speos/core/sensor.py src/ansys/speos/core/project.py tests/core/test_sensor.py
python -m pytest tests/core/test_sensor.py -k <sensor-keyword> -q --maxfail=1
```

Example keyword: `observer`.

---

## Related contributor guides

- `/.github/agents/implement-feature.md`
- `/.github/agents/write-tests.md`
- `/.github/agents/fix-bug.md`


