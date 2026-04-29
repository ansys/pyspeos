# Agent Task: Implement a New PySpeos Feature

Use this prompt file in GitHub Copilot Workspace (or any AI coding agent) when asked to add a
new source type, sensor type, simulation type, optical property variant, or similar domain object.

---

## Step-by-step workflow

### Step 1 — Add a parameter dataclass

**File:** `src/ansys/speos/core/generic/parameters.py`

- Create a `@dataclass` named `<Feature><Variant>Parameters`.
- Add typed fields with sensible default values.
- Add inline comments or a class docstring explaining what each field controls.
- Import any enums or helpers already defined in the same file.

```python
@dataclass
class SourceSphereParameters:
    """Parameters for :class:`SourceSphere`.

    Parameters
    ----------
    flux_value : float, optional
        Total luminous flux in lm. Default is ``683.0``.
    """
    flux_value: float = 683.0
```

### Step 2 — Implement the feature class

**File:** `src/ansys/speos/core/source.py` (or the appropriate domain module)

1. Subclass the matching `Base*` class (e.g. `BaseSource`, `BaseSensor`, `BaseSimulation`).
2. Write a NumPy-style class docstring with `Parameters` and `Notes` sections.
3. Implement properties as `@property` getter / `<name>.setter` pairs that read/write the
   underlying protobuf message stored in `self._source_template` (or equivalent).
4. Add a `_fill_parameters(self, default_parameters=None)` method that accepts a parameters
   dataclass and applies defaults.
5. Guard nested configuration inner classes with `stable_ctr: bool = False` and raise
   `RuntimeError` when the caller bypasses the parent's setter methods.
6. Apply `@min_speos_version(major, minor)` from `generic/general_methods.py` to any method
   that requires a minimum server version.

### Step 3 — Register in the Project factory

**File:** `src/ansys/speos/core/project.py`

- Locate the `create_source()` / `create_sensor()` / `create_simulation()` method.
- Add the new type name to the dispatch (`match type_name` or `if/elif` block).
- Instantiate the new class and return it.

### Step 4 — Export the public symbol

**File:** `src/ansys/speos/core/__init__.py`

Add an explicit import if end-users are expected to reference the class directly:

```python
from ansys.speos.core.source import SourceSphere
```

### Step 5 — Write tests

**File:** `tests/core/test_source.py` (or matching domain test file)

- Use fixtures from `tests/conftest.py` (`speos`, `project`).
- Test default construction (no parameters), construction with a parameters dataclass,
  and key property setters / getters.
- Round-trip through `commit()` and re-read to verify server-side persistence where applicable.

See [write-tests.md](write-tests.md) for full test conventions.

### Step 6 — Apply code quality

- Add the MIT SPDX license header to any **new** `.py` file.
- Run `ruff check --fix` and `ruff format`.
- Confirm all public symbols have NumPy docstrings.
- Add a changelog fragment in `doc/changelog.d/<issue-number>.added.md`.

---

## Reference: existing patterns to copy

| What you need | File to look at |
|---|---|
| Parameter dataclass | `generic/parameters.py` → `SourceLuminaireParameters` |
| Feature class with inner config classes | `source.py` → `SourceLuminaire` |
| `@min_speos_version` usage | `source.py` → `SourceRayFile` |
| Factory dispatch | `project.py` → `create_source()` |
| Test fixture usage | `tests/core/test_source.py` |

