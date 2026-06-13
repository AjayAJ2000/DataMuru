# Configuration Model

The alpha configuration model is anchored by `datamuru.yml` at the repository root.

## Root configuration

The root config declares:

- Project metadata
- Environment references
- Default environment
- Feature toggles
- State backend settings
- Provider settings
- Optional AI-related switches

## Supporting files

The root file points to or works alongside:

- `environments/*.yml`
- `providers/*.yml`
- `workspaces/*.yml`
- `governance/*.yml`

## Design goals

The configuration model is designed to be:

- Readable by humans
- Stable enough for editors and schema tooling
- Expandable without breaking existing alpha assumptions

## Validation in the alpha

Validation currently uses manual alpha-aware checks plus published schema artifacts under `schemas/`.

This is a pragmatic bootstrap step:

- enough to enforce structure
- small enough to evolve safely
- explicit enough to document cleanly
