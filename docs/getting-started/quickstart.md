# Five-minute local quickstart

This quickstart runs entirely on your computer. It does not require credentials
and does not contact Databricks.

## 1. Create a clean environment

=== "Windows PowerShell"

    ```powershell
    mkdir datamuru-quickstart
    cd datamuru-quickstart
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install datamuru==0.1.0a0
    ```

=== "macOS or Linux"

    ```bash
    mkdir datamuru-quickstart
    cd datamuru-quickstart
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    pip install datamuru==0.1.0a0
    ```

Verify the installation:

```console
$ datamuru --help
Usage: datamuru [OPTIONS] COMMAND [ARGS]...
```

## 2. Initialize a project

```powershell
datamuru init --name quickstart --output-dir .
```

The command creates a root configuration and supporting directories. Keep the
provider in `state-only` mode for this tutorial.

## 3. Validate the configuration

```powershell
datamuru validate --config datamuru.yml --strict
```

Expected result:

```text
Configuration is valid.
```

`--strict` treats warnings as a failed validation. It is useful in CI and team
workflows.

## 4. Review the plan

```powershell
datamuru plan --config datamuru.yml
```

The first plan uses `+`, `~`, `=`, and `-` to represent create, update, no-op,
and destroy actions. Review every destroy action before continuing.

## 5. Apply to local state

```powershell
datamuru apply --config datamuru.yml --auto-approve
```

In `state-only` mode, apply records the desired resources in the configured
local state file. It does not create cloud resources.

## 6. Verify idempotency

```powershell
datamuru plan --config datamuru.yml
```

Expected result: declared resources report `resource already matches` or the
plan contains no required changes.

## What you learned

You completed DataMuru's core loop: initialize, validate, plan, apply, and
re-plan.

Next, [connect a Databricks workspace](../tutorials/connect-databricks.md) in
`live-readonly` mode.
