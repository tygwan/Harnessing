# Transcript Ingestion Spec

## Goal

Define a minimal transcript ingestion boundary for Harnessing so Codex and Claude Code session artifacts can be indexed as reusable memory entries.

The first implementation should be simple, inspectable, and easy to expand.

## Supported Inputs

- `.jsonl`
- `.txt`
- `.md`
- `.log`

Inputs may be a single file or a directory.

## Format Boundary

### JSONL

Each line is one transcript event object.

Expected fields:

- `content`
- `speaker`
- `role`
- `kind`
- `timestampUtc`
- `tags`

Optional fields are allowed and ignored if not needed.

### Text / Markdown

Plain text transcripts are split into blocks separated by blank lines.

The first pass treats each non-empty block as one transcript event.

## Normalized Transcript Record

Each ingested transcript item should normalize to a record with:

- `sourcePath`
- `sourceKind`
- `entryKind`
- `speaker`
- `content`
- `tags`
- `origin = transcript`

## Entry Kinds

The first version should recognize these kinds:

- `transcript-entry`
- `transcript-message`
- `transcript-tool`
- `transcript-decision`
- `transcript-reflection`
- `transcript-technique`

## Storage Strategy

Transcript entries are stored as reusable memory records first.

This keeps the prototype small while still making transcript content searchable through the existing memory engine.

## Future Expansion

- preserve raw transcript artifacts separately
- add tool-write event extraction
- add summary generation over transcript batches
- add transcript-to-decision and transcript-to-technique promotion rules
