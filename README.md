# Harnessing

![Windows First](https://img.shields.io/badge/platform-Windows%20first-0f766e)
![Python](https://img.shields.io/badge/python-3.11%2B-2563eb)
![Storage](https://img.shields.io/badge/storage-SQLite%20FTS5-7c3aed)
![Interface](https://img.shields.io/badge/interface-CLI%20first-f59e0b)

Reusable project memory, search, and context bundle engine for Codex and Claude Code.

## Why

Large projects slow down when every session has to reload too much context.

Harnessing keeps high-value project memory small, searchable, and reusable by combining:

- `memento`
- project docs
- derived memory entries
- transcript-derived memories
- compact context bundles

## What It Does

- ingests project docs into a local SQLite/FTS index
- derives reusable memory entries from status, testing, troubleshooting, and memento docs
- ingests transcript files into searchable memory entries
- emits `lean`, `work`, and `deep` context bundles with token-aware budgets
- prefers reusable memory over duplicate raw doc sections

## Architecture

```text
Consumer Repo Artifacts
  -> Ingestion
     -> sections
     -> derived memories
     -> transcript memories
  -> Retrieval
     -> search
     -> context
     -> bundle
  -> Agent Consumption
     -> Codex
     -> Claude Code
```

## Why CLI First

Harnessing starts as a CLI-first core engine because it keeps the memory layer easy to verify and easy to embed later.

- testable one step at a time
- immediately callable from local agent workflows
- clean foundation for later HTTP APIs, hooks, and editor integrations

## Platform Policy

Harnessing is currently `Windows-first`.

- development and verification start on Windows
- macOS and Linux are planned later
- the core stays portable where practical, but non-Windows support is not yet a delivery target

## Quick Start

```powershell
python src/harnessing/cli.py init
python src/harnessing/cli.py ingest
python src/harnessing/cli.py stats
python src/harnessing/cli.py search "document delta"
python src/harnessing/cli.py context "diagnostics requestId" --limit 3 --mode work
python src/harnessing/cli.py bundle "backend actions externalevent" --limit 4 --mode lean
python src/harnessing/cli.py transcript ingest --source <path>
```

## Bundle Modes

| Mode | Use | Goal |
|------|-----|------|
| `lean` | session startup | minimum token cost |
| `work` | active implementation | balanced detail |
| `deep` | debugging and review | fuller context |

Each bundle reports:

- selected item count
- char usage
- estimated token count

## Current Shape

- package: `src/harnessing`
- docs: `docs/`
- local runtime state: `.harnessing/`

## First Consumer

`ontology-for-cm` is the proving-ground consumer for Harnessing.

The working model is:

```text
ontology-for-cm proves a useful pattern
  -> Harnessing generalizes it
  -> ontology-for-cm consumes it again
```

## Docs

- [Documentation System](./docs/README.md)
- [Architecture](./docs/tech-specs/ARCHITECTURE.md)
- [Platform Support](./docs/tech-specs/PLATFORM-SUPPORT.md)
- [Dual-Track Operating Model](./docs/tech-specs/DUAL-TRACK-OPERATING-MODEL.md)
- [Consumer Integration Contract](./docs/tech-specs/CONSUMER-INTEGRATION-CONTRACT.md)
- [Transcript Ingestion Spec](./docs/tech-specs/TRANSCRIPT-INGESTION-SPEC.md)
- [Smoke Test](./docs/testing/SMOKE-TEST.md)
- [Transcript Ingestion Test](./docs/testing/TRANSCRIPT-INGESTION-TEST.md)

## Near-Term Focus

- strengthen transcript parsing and memory promotion
- add tool-write and edit-event ingestion
- add machine-readable context bundle export
- keep token usage low while improving retrieval quality
