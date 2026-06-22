# PySpeos — GitHub Copilot Instructions

## Project Overview

PySpeos (`ansys-speos-core`) is a Python gRPC wrapper around the Ansys Speos optics simulation
server. It exposes Speos features (sources, sensors, simulations, optical properties, geometry)
as Pythonic classes that communicate with a running Speos gRPC server via `ansys-api-speos`
protobuf stubs.

The package follows the **PyAnsys** standards for structure, documentation, and testing.

---

## Repository Layout

```
src/ansys/speos/core/          ← Main package (one module per domain)
  source.py                    ← Light sources (Luminaire, Surface, RayFile, Ambient variants)
  sensor.py                    ← Sensors (Irradiance, Camera, Radiance, XMPIntensity, 3DIrradiance)
  simulation.py                ← Simulations (Direct, Inverse, Interactive, VirtualBSDF)
  opt_prop.py                  ← Optical surface properties
  spectrum.py                  ← Spectrum sub-feature helpers
  intensity.py                 ← Intensity distribution sub-feature helpers
  project.py                   ← Top-level Project object (owns all features)
  speos.py                     ← Speos client entry point (gRPC connection)
  geo_ref.py                   ← Geometry reference helpers
  generic/
    parameters.py              ← @dataclass parameter objects (defaults for every feature)
    general_methods.py         ← Decorators: @min_speos_version, @graphics_required, etc.
  kernel/                      ← Low-level protobuf wrappers (ProtoScene, ProtoSourceTemplate…)

tests/
  conftest.py                  ← Shared pytest fixtures (speos, project, stubs)
  assets/                      ← Test input files (IES, OPTMat, spectrum CSV, …)
  core/                        ← Unit/integration tests (test_source.py, test_sensor.py, …)

doc/
  source/                      ← Sphinx RST documentation
examples/                      ← Jupyter notebook examples (core/, kernel/, workflow/)
```

---

## Architecture Pattern

Every Speos feature is implemented in three layers:

| Layer | Location | Role |
|---|---|---|
| **Kernel** | `kernel/` | Thin gRPC stub wrappers; CRUD on protobuf messages |
| **Feature** | `source.py`, `sensor.py`, … | Pythonic classes with properties and fluent setters |
| **Parameters** | `generic/parameters.py` | `@dataclass` objects holding default values |

The `Project` class in `project.py` provides factory methods (`create_source()`,
`create_sensor()`, `create_simulation()`) that orchestrate creation and register features
into the Speos scene.

### Nested class guard pattern

Inner configuration classes (e.g. `SourceLuminaire.FluxFromLuminousFlux`) that must only be
created via the parent class use a `stable_ctr: bool` constructor argument:

```python
class _MyInner:
    def __init__(self, stable_ctr: bool = False):
        if not stable_ctr:
            raise RuntimeError("Use parent.set_*() to configure this object.")
```

---

## Coding Standards

- **Python ≥ 3.10** — use `match`/`case`, `|` in type hints, `from __future__ import annotations`.
- **Linting**: `ruff` (see `pyproject.toml`). Run `ruff check --fix` and `ruff format` before
  committing. Fix all warnings — CI enforces zero violations.
- **Docstrings**: NumPy style on every public class, method, and property.
  Required sections: `Parameters`, `Returns` (when non-`None`), `Notes` (for caveats).
- **License header**: Every `.py` file must start with the MIT SPDX header block. Copy it from
  any existing file in `src/ansys/speos/core/`.
- **Imports order**: standard library → third-party → `ansys.api.speos` stubs →
  `ansys.speos.core` internals. Use `isort` (via `ruff`) to enforce this.
- **Type hints**: Annotate all public method signatures.
- **`@min_speos_version(major, minor)`**: Decorate any method that requires a minimum Speos
  server version. See `generic/general_methods.py`.
- **`@graphics_required`**: Decorate methods that need a graphical Speos session.

---

## Common Tasks

### Add a new source / sensor / simulation type

1. Add a `@dataclass` to `generic/parameters.py` named `<Feature><Variant>Parameters`.
2. Add a subclass of `BaseSource` / `BaseSensor` / `BaseSimulation` in the relevant domain module.
3. Register the new type in `project.py`'s `create_*()` factory dispatch.
4. Export from `src/ansys/speos/core/__init__.py` if users should import it directly.
5. Add tests in `tests/core/test_<domain>.py`.
6. Add a usage example in `examples/` if the feature is user-facing.

### Create or update an example

- Prefer updating the existing domain example first (for example, add new source walkthroughs to
  `examples/core/source.py`) instead of creating a brand new example file for every small feature.
- Follow the tutorial style already used in `examples/`: short narrative headings, incremental code
  blocks, and `print()` calls that show defaults before and after `commit()` when useful.
- Reuse repository assets from `tests/assets/` or existing example assets whenever possible; avoid
  introducing new assets unless they are required to demonstrate the feature.
- If the example creates intermediate objects such as spectra or intensity templates, include
  cleanup consistent with the rest of the file.
- If you add a brand new example file, also register it in `doc/source/examples.rst` so it appears
  in the examples gallery.

### Add a parameter dataclass

File: `src/ansys/speos/core/generic/parameters.py`

```python
from dataclasses import dataclass, field

@dataclass
class SourceLuminaireParameters:
    """Parameters for :class:`SourceLuminaire`.

    Parameters
    ----------
    flux_type : str, optional
        Flux type. Accepted values: ``"LuminousFlux"``, ``"Radiant"``, ``"LuminousIntensity"``.
    flux_value : float, optional
        Flux magnitude in the unit implied by *flux_type*.
    """
    flux_type: str = "LuminousFlux"
    flux_value: float = 683.0
```

### Write or update tests

See [`.github/agents/write-tests.md`](.github/agents/write-tests.md).

### Implement a new feature end-to-end

See [`.github/agents/implement-feature.md`](.github/agents/implement-feature.md).

### Fix a bug

See [`.github/agents/fix-bug.md`](.github/agents/fix-bug.md).

---

## PR Checklist

Commit titles must follow **Conventional Commits**:
`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `ci:`

Before opening a PR:

- [ ] `ruff check --fix` and `ruff format` pass with no errors.
- [ ] Every new public symbol has a NumPy docstring.
- [ ] New or changed behaviour is covered by tests.
- [ ] MIT license header is present on all new `.py` files.
- [ ] A changelog fragment is added in `doc/changelog.d/` (see existing fragments for format).

