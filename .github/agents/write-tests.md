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
| `project` | `Project` | Blank `Project` attached to `speos`. Scoped per test. |
| `tmp_path` | `Path` | pytest built-in — temporary directory for output files. |

**Never** instantiate `Speos` or `Project` directly inside a test. Always use fixtures.

---

## Test structure

```python
def test_source_luminaire_default_flux(project):
    """Verify that a new SourceLuminaire has the documented default flux value."""
    src = project.create_source("Luminaire", name="test_src")
    assert src.flux_type == "LuminousFlux"
    assert src.flux_value == pytest.approx(683.0)


def test_source_luminaire_set_flux(project):
    """Verify that setting flux_value persists after commit."""
    src = project.create_source("Luminaire", name="test_src")
    src.flux_value = 1000.0
    src.commit()
    reloaded = project.get_source("test_src")
    assert reloaded.flux_value == pytest.approx(1000.0)
```

Each test should:
1. Create the feature under test via `project.create_*()`.
2. Assert the **default state** matches the documented defaults.
3. Exercise **setters** and assert the new state.
4. Where applicable, round-trip through `commit()` and re-read to verify server-side persistence.

---

## Markers

- `@pytest.mark.speos` — requires a live Speos server; CI skips if server is unavailable.
- `@pytest.mark.parametrize` — use to cover multiple enum values of the same property.

```python
@pytest.mark.parametrize("flux_type", ["LuminousFlux", "Radiant", "LuminousIntensity"])
def test_source_luminaire_flux_types(project, flux_type):
    """Verify all supported flux type values can be set."""
    src = project.create_source("Luminaire", name=f"src_{flux_type}")
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
- Reference them via `pathlib.Path(__file__).parent.parent / "assets" / "my_file.ies"`.
- Never use absolute paths in tests.

---

## Docstrings

Every test function must have a **one-line docstring** that describes what it verifies:

```python
def test_source_rayfile_ies_path(project, tmp_path):
    """Verify that an IES file path round-trips through commit() correctly."""
```

