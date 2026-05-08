# Agent Task: Write Tests for a PySpeos Feature

Use this prompt file when asked to add or improve pytest coverage for any PySpeos module.

---

## Test file locations

| Domain | Test file |
|---|---|
| Sources | `tests/core/test_source.py` |
| Sensors | `tests/core/test_sensor.py` |
| Simulations | `tests/core/test_simulation.py` |
| Optical properties | `tests/core/test_opt_prop.py` |
| Spectrum / Intensity | `tests/core/test_spectrum.py` / `tests/core/test_intensity.py` |

---

## Fixtures

All fixtures are defined in `tests/conftest.py`. Key fixtures:

| Fixture | Type | Description |
|---|---|---|
| `speos` | `Speos` | Connected Speos gRPC client (or stub). Scoped to the test session. |
| `tmp_path` | `Path` | pytest built-in — temporary directory for output files. |
| `test_path` | `Path | str` | Asset root path imported from `tests.conftest` (local or Docker path). |

Always use the `speos` fixture in test signatures, and then create a project in the test body:

```python
p = Project(speos=speos)
```

For load tests, pass the project path at creation time.

---

## Test structure

```python
def test_source_luminaire_default_flux(speos: Speos):
    """Verify that a new SourceLuminaire has the documented default flux value."""
    p = Project(speos=speos)
    src = p.create_source(name="test_src", feature_type=SourceLuminaire)
    assert src.flux_type == "LuminousFlux"
    assert src.flux_value == pytest.approx(683.0)


def test_source_luminaire_set_flux(speos: Speos):
    """Verify that setting flux_value persists after commit."""
    p = Project(speos=speos)
    src = p.create_source(name="test_src", feature_type=SourceLuminaire)
    src.flux_value = 1000.0
    src.commit()
    reloaded = p.find(name="test_src", feature_type=SourceLuminaire)[0]
    assert reloaded.flux_value == pytest.approx(1000.0)
```

Each test should:
1. Create a local project via `Project(speos=speos)`.
2. Create the feature under test via `p.create_*()`.
3. Assert the **default state** matches the documented defaults.
4. Exercise **setters** and assert the new state.
5. Where applicable, round-trip through `commit()` and re-read to verify server-side persistence.

---

## Load-from-asset tests

For tests that validate loading existing `.speos` projects, follow this pattern:

```python
def test_source_ambient_uniform_load(speos: Speos):
    """Verify ambient uniform sources are loaded with expected API and backend values."""
    p = Project(
        speos=speos,
        path=str(Path(test_path) / "Source.speos" / "SourceUniformTests.speos"),
    )

    for src in p.sources:
        ...
```

For load tests, validate both:
- public API values (`luminance`, `mirrored_extent`, etc.)
- backend protobuf values (`HasField(...)`, expected subtype/value)

---

## Markers

- `@pytest.mark.supported_speos_versions(min=...)` for version-gated tests
- optional `max=...` for deprecated/discontinued behavior

The test suite auto-adds `all_speos_versions` to unmarked tests in `tests/conftest.py`.

Use `@pytest.mark.parametrize` when it improves clarity for repeated enum/value checks.

```python
@pytest.mark.supported_speos_versions(min=252)
@pytest.mark.parametrize("flux_type", ["LuminousFlux", "Radiant", "LuminousIntensity"])
def test_source_luminaire_flux_types(speos: Speos, flux_type):
    """Verify all supported flux type values can be set."""
    p = Project(speos=speos)
    src = p.create_source(name=f"src_{flux_type}", feature_type=SourceLuminaire)
    src.flux_type = flux_type
    assert src.flux_type == flux_type
```

---

## Naming conventions

- Function names: `test_<class_name_snake>_<scenario>`.
  Examples: `test_source_luminaire_default_flux`, `test_sensor_irradiance_set_resolution`.
- Avoid generic names like `test_1`, `test_case_a`, `test_it`.

---

## Test assets

- Place input files (IES photometry, OPTMat files, spectrum CSVs) in `tests/assets/`.
- Reference assets via `test_path`:

```python
from tests.conftest import test_path

asset = Path(test_path) / "IES_C_DETECTOR.ies"
```

- Never hardcode machine-specific absolute paths in tests.

---

## Docstrings

Every test function must have a **one-line docstring** that describes what it verifies:

```python
def test_source_rayfile_ies_path(speos: Speos, tmp_path):
    """Verify that an IES file path round-trips through commit() correctly."""
```

