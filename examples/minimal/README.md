# Minimal Example

This folder is a complete state-only OSS project. It does not contact Databricks.

Run from this directory:

```bash
datamuru validate --config datamuru.yml --strict
datamuru plan --config datamuru.yml
datamuru apply --config datamuru.yml --auto-approve
datamuru plan --config datamuru.yml
```

The second plan should report the declared resources as already matching.
