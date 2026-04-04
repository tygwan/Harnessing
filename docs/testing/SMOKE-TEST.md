# Smoke Test

Run from the repository root.

```powershell
python src/harnessing/cli.py init
python src/harnessing/cli.py ingest
python src/harnessing/cli.py transcript ingest --source <path>
python src/harnessing/cli.py stats
python src/harnessing/cli.py search "memory harness"
python src/harnessing/cli.py bundle "transcript ingestion" --limit 3 --mode lean
python src/harnessing/cli.py bundle "transcript ingestion" --limit 3 --mode work
```

## Expected Result

- SQLite DB is created under `.harnessing/memory.db`
- ingestion succeeds
- transcript ingestion can add transcript-derived memories
- search returns doc or memory hits
- bundle returns compact markdown context
- lean bundle should report lower estimated token usage than work bundle for the same query

