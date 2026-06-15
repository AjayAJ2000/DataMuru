# Python API

The `DataMuru` class wraps the same engine used by the CLI.

```python
from datamuru.api import DataMuru

dm = DataMuru("datamuru.yml")
issues = dm.validate()
report = dm.doctor()
plan = dm.plan(target="catalog:analytics")
```

## Constructor

```python
DataMuru(config_path: str | Path, environment: str | None = None)
```

## Methods

| Method | Result |
| --- | --- |
| `validate()` | validation issues |
| `doctor()` | `DoctorReport` |
| `edition_summary()` | `EditionSummary` |
| `plan(target=None)` | `Plan` |
| `save_plan(output_path, target=None)` | saved-plan result |
| `apply(target=None)` | `ApplyResult` |
| `apply_saved_plan(plan_path)` | `ApplyResult` |
| `destroy(target=None)` | `ApplyResult` |
| `import_discover(include_system=False)` | `ImportDiscoveryReport` |
| `import_generate(...)` | generated workspace configuration result |
| `import_adopt(targets=[...], commit=False)` | `ImportAdoptionResult` |

## Example: guarded apply

```python
from datamuru.api import DataMuru

dm = DataMuru("datamuru.yml")

if not dm.doctor().success:
    raise RuntimeError("Provider diagnostics failed")

plan = dm.plan(target="catalog:analytics")
destructive = [change for change in plan.changes if change.action == "destroy"]
if destructive:
    raise RuntimeError("Review destroy actions before apply")

result = dm.apply(target="catalog:analytics")
```

The Python contracts are alpha APIs. Pin the package version and test upgrades.
