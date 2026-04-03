# Platform Support

## Policy

Harnessing starts as a `Windows-first` project.

This means:

- primary development happens on Windows
- smoke tests and early integrations are validated on Windows first
- documentation examples may prefer PowerShell in the early phase

## Planned Support

Other platforms are planned, but not committed for the first delivery phase.

- macOS: planned
- Linux: planned

## Reasoning

The current proving ground is `ontology-for-cm`, which is already being developed and tested on Windows with:

- Revit 2026
- Visual Studio
- local PowerShell workflows

So the harness should first become stable in the environment where it is immediately useful.

## Engineering Rule

Even with a Windows-first policy, the core engine should avoid unnecessary platform lock-in where practical.

Examples:

- prefer Python standard library
- prefer `pathlib`
- keep storage local and simple with SQLite
- avoid Windows-only APIs in the core engine unless required

## Revisit Point

Once transcript ingestion and project integration contracts are stable, revisit the platform policy and add explicit macOS/Linux validation work.
