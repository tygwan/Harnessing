# Consumer Integration Contract

## Purpose

This document defines the contract between `Harnessing` and a consumer repository such as `ontology-for-cm`.

The goal is to keep the reusable harness generic while giving consuming projects a predictable way to feed source artifacts and consume context outputs.

## Model

```text
consumer repo artifacts
  -> Harnessing ingest
  -> local sections + memories
  -> search / context / bundle
  -> agent workflow consumption
```

## Consumer Responsibilities

A consumer repository should provide stable, readable source artifacts.

Preferred sources:

- `README.md`
- `.codex/MEMENTO.md`
- `docs/**/*.md`
- project-local testing guides
- troubleshooting logs
- decision or architecture records

Optional future sources:

- transcripts
- tool-write or edit event logs
- machine-readable issue summaries

## Harnessing Responsibilities

Harnessing should:

- ingest supported source artifacts without requiring project-specific code
- classify sections and memories predictably
- expose stable CLI outputs for search, context, and bundle generation
- keep runtime state local and uncommitted
- avoid mutating consumer project source files

## Runtime Boundary

Harnessing owns:

- `.harnessing/memory.db`
- ingest rules
- memory derivation rules
- search and bundle outputs

Consumer repos own:

- source documentation
- memento files
- tests and troubleshooting logs
- domain-specific decisions

## Initial CLI Contract

The consumer-facing commands should remain stable enough for reuse:

```powershell
python src/harnessing/cli.py init
python src/harnessing/cli.py ingest --source <path>
python src/harnessing/cli.py search "<query>"
python src/harnessing/cli.py context "<query>"
python src/harnessing/cli.py bundle "<query>"
python src/harnessing/cli.py stats
```

## First Consumer: ontology-for-cm

`ontology-for-cm` acts as the proving-ground consumer.

Current expected source artifacts:

- `.codex/MEMENTO.md`
- `docs/status/CURRENT.md`
- `docs/status/CHANGELOG.md`
- `docs/testing/*.md`
- `docs/troubleshooting/*.md`
- `docs/tech-specs/*.md`

Expected value:

- faster task startup
- easier reuse of troubleshooting and test knowledge
- more consistent project memory across Codex and Claude Code sessions

## Integration Rule

Do not move domain-specific ontology or Revit logic into Harnessing.

Move functionality into Harnessing only when it is:

- generic
- reusable by more than one project
- part of memory ingestion, retrieval, or context generation

## Next Contract Extensions

- transcript file format
- machine-readable context bundle export
- memory type taxonomy
- consumer repo onboarding checklist
