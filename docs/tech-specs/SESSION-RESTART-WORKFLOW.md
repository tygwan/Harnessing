# Session Restart Workflow

## Purpose

Define the minimum workflow required to resume work after a fresh `/new` session without rereading the whole codebase.

## Current Position

Harnessing is currently:

- `recovery-ready`
- not yet `fully automatic`

That means a new session can recover direction and active work quickly, but it still relies on a deliberate startup routine.

## Current Restart Loop

```text
open consumer repo
  -> open Harnessing repo
  -> ingest latest docs and memory artifacts
  -> query for current status and next target
  -> generate a lean or work bundle
  -> continue implementation
```

## Minimum Startup Procedure

For a consumer such as `ontology-for-cm`:

1. open the consumer repo and Harnessing repo
2. run `python src/harnessing/cli.py ingest`
3. run a query such as:
   - `current status`
   - `next engineering target`
   - `revit backend actions`
4. generate a bundle:
   - `--mode lean` for fast recovery
   - `--mode work` for active implementation
5. continue work using the recovered context

## What This Already Solves

- avoids rereading large parts of the codebase
- reloads direction, status, and troubleshooting context quickly
- keeps token usage lower than raw doc or transcript injection

## What It Does Not Yet Solve

- automatic startup bundle generation
- project-specific alias presets
- transcript and tool-write prioritization strong enough for every session
- guaranteed one-command continuity

## Next Improvements

- add consumer-specific startup presets
- promote more transcript content into reusable memories
- add stronger alias and synonym handling for common project questions
- add export formats that can be injected into Codex and Claude Code with less manual steering
