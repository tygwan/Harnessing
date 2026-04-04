# Architecture

## Core Layers

```text
Project Sources
  -> Ingestion Layer
  -> SQLite Storage
  -> Search and Retrieval
  -> Context Bundle Output
  -> Agent Consumption
```

## Current Storage Layers

- `sections`
  - heading-based source document sections
- `memories`
  - derived or manually captured memory entries
- transcript items are normalized into `memories` first in the current prototype

## Retrieval Policy

- prefer `memory` hits before duplicate `doc` hits
- prefer derived memories over raw transcript entries
- keep transcript-derived entries as fallback context, not the first default payload

## Bundle Policy

Bundle generation supports:

- `lean`
- `work`
- `deep`

Each bundle reports:

- selected item count
- char usage
- estimated token count

## Runtime State

- local DB path: `.harnessing/memory.db`
- repo-local and intentionally ignored by Git
