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
| `state_backend_report()` | state backend readiness report |
| `enterprise_activation_report()` | activation readiness report |
| `enterprise_activation_purchase_request()` | redacted purchase/license activation request |
| `enterprise_activation_evidence_report()` | redacted activation audit evidence report |
| `enterprise_activation_handoff_package(output_dir)` | redacted activation handoff package manifest |
| `enterprise_control_plane_contract()` | hosted control plane handoff contract |
| `enterprise_control_plane_architecture()` | hosted control plane reference architecture |
| `write_enterprise_activation_bundle(output_path)` | redacted activation handoff bundle path |
| `write_enterprise_activation_purchase_request(output_path)` | redacted purchase/license activation request path |
| `write_enterprise_activation_evidence(output_path)` | redacted activation audit evidence path |
| `write_enterprise_activation_handoff_package(output_dir)` | redacted activation handoff package manifest |
| `write_enterprise_control_plane_contract(output_path)` | redacted hosted control plane contract path |
| `write_enterprise_control_plane_architecture(output_path)` | hosted control plane architecture path |
| `plan(target=None)` | `Plan` |
| `save_plan(output_path, target=None)` | saved-plan result |
| `apply(target=None)` | `ApplyResult` |
| `apply_saved_plan(plan_path)` | `ApplyResult` |
| `destroy(target=None)` | `ApplyResult` |
| `import_discover(include_system=False, catalogs=None, progress=None)` | `ImportDiscoveryReport` |
| `import_generate(...)` | generated workspace configuration result |
| `import_adopt(targets=[...], commit=False)` | `ImportAdoptionResult` |

`progress` is an optional callback that receives dictionaries such as
`{"message": "...", "total": 12, "completed": 5}`. CLI text output uses this to
render import progress while keeping JSON output machine-readable.

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
