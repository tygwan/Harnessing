# Harnessing

Shared memory harness for agent-driven development workflows.

## Purpose

Harnessing combines:

- `memento`
- project docs
- derived memory entries
- local search
- compact context bundles

The goal is to give Codex and Claude Code a reusable local memory/context layer without requiring the full codebase to be loaded on every task.

## Current Shape

This repository starts as a CLI-first core engine.

Why CLI first:

- the memory engine can be tested step by step
- local workflows for Codex and Claude Code can call it immediately
- later interfaces such as HTTP APIs, editor integrations, and hooks can be added on top of the same core

## Platform Policy

Harnessing is currently `Windows-first`.

- primary development and verification start on Windows
- macOS and Linux are planned later
- the core engine is kept portable where practical, but non-Windows support is not yet a delivery target

## Package Layout

- `src/harnessing`
  - reusable Python package
- `docs`
  - direction, planning, status, testing, and technical specs
- `.harnessing`
  - local runtime state such as SQLite databases

## Core Commands

```powershell
python src/harnessing/cli.py init
python src/harnessing/cli.py ingest
python src/harnessing/cli.py stats
python src/harnessing/cli.py search "document delta"
python src/harnessing/cli.py context "diagnostics requestId" --limit 3
python src/harnessing/cli.py bundle "backend actions externalevent" --limit 4
python src/harnessing/cli.py capture --kind decision --title "Example" --summary "Short summary"
```

## Initial Target

The first target is a portable SQLite/FTS memory engine that can be validated in `ontology-for-cm` and then reused across projects.

