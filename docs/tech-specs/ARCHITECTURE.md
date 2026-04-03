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

## Runtime State

- local DB path: `.harnessing/memory.db`
- repo-local and intentionally ignored by Git
