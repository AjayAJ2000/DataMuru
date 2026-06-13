# Python API

The current public Python entrypoint is:

```python
from datamuru import DataMuru
```

## Primary operations

### Validate

```python
dm = DataMuru(config_path="datamuru.yml")
issues = dm.validate()
```

### Plan

```python
plan = dm.plan()
```

### Doctor

```python
report = dm.doctor()
```

### Apply

```python
result = dm.apply()
```

### Destroy

```python
result = dm.destroy()
```

## API philosophy

The alpha keeps the Python API intentionally close to the core orchestration model:

- simple constructor
- explicit config path
- direct operational methods
- the same live-readiness rules as the CLI

This keeps the CLI and Python usage aligned and makes future API evolution easier to document.
