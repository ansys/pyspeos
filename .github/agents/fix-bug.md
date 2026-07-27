# Agent Task: Fix a Bug in PySpeos

Use this prompt file when asked to investigate and fix a failing test, a reported exception,
or incorrect behaviour in any PySpeos module.

---

## Workflow

### Step 1 — Reproduce the failure

- If a failing test is provided, run it first to confirm the failure:
  ```
  pytest tests/core/test_source.py::test_source_luminaire_default_flux -v
  ```
- Note the full traceback and the line numbers involved.

### Step 2 — Trace the call stack

Follow the call chain from the failing assertion downward:

1. **Feature layer** (`source.py`, `sensor.py`, …) — locate the property or method.
2. **Kernel layer** (`kernel/`) — identify which protobuf message field is being read/written.
3. **Protobuf stub** (`ansys.api.speos` package) — verify the field name and type in the
   generated stub or `.proto` definition.

Common causes:

| Symptom | Likely cause |
|---|---|
| `AttributeError` on protobuf object | Field name changed in a new `ansys-api-speos` version |
| Value returned is `0` or default | Setter writes to a different oneof branch than the getter reads |
| `RuntimeError: stable_ctr` | Inner class instantiated directly instead of via parent setter |
| gRPC `StatusCode.NOT_FOUND` | Feature not registered / committed before being referenced |

### Step 3 — Apply the fix

- Make the minimal change necessary.
- If a protobuf field was renamed, update **all** usages across the domain module and tests.
- Do **not** change unrelated code in the same PR.

### Step 4 — Verify

1. The previously failing test now passes.
2. The full test file still passes: `pytest tests/core/test_<domain>.py -v`.
3. `ruff check --fix` and `ruff format` produce no errors.

### Step 5 — Add a regression test

Add a test that would have caught this bug:

```python
def test_source_luminaire_flux_value_roundtrip(project):
    """Regression: flux_value must survive commit/reload (fixed in #<issue>)."""
    src = project.create_source("Luminaire", name="reg_test")
    src.flux_value = 500.0
    src.commit()
    assert project.get_source("reg_test").flux_value == pytest.approx(500.0)
```

### Step 6 — Add a changelog fragment

Create `doc/changelog.d/<issue-number>.fixed.md`:

```markdown
Fixed ``SourceLuminaire.flux_value`` returning 0 after ``commit()`` when using Speos 2025 R2.
```

---

## Useful debugging helpers

- `source._source_template` — the raw protobuf `SourceTemplate` message.
- `project._speos.client` — the live gRPC channel for direct stub calls.
- `kernel/` modules expose `_get()` / `_update()` / `_delete()` helpers for protobuf CRUD.

