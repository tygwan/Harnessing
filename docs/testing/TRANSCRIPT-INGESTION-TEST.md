# Transcript Ingestion Test

## Purpose

Verify that Harnessing can ingest transcript files and promote them into searchable memory entries.

## Test Inputs

- a `.jsonl` transcript file
- a plain text or markdown transcript file

## Steps

1. Run `python src/harnessing/cli.py init`
2. Run `python src/harnessing/cli.py transcript ingest --source <path>`
3. Run `python src/harnessing/cli.py stats`
4. Run `python src/harnessing/cli.py memories --limit 10`
5. Run `python src/harnessing/cli.py search "<speaker or tool term>"`
6. Run `python src/harnessing/cli.py bundle "<topic>"`

## Expected Result

- transcript items are stored in `memories`
- search returns transcript-derived hits
- the bundle output contains compact transcript context

## Result Template

```text
Test: Transcript Ingestion
Input Format:
Observed Ingest Result:
Observed Stats:
Observed Memory Entries:
Observed Search Result:
Observed Bundle Result:
Pass/Fail:
Notes:
```
