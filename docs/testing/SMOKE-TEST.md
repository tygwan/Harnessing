# Smoke Test

Run from the repository root.

```powershell
python src/harnessing/cli.py init
python src/harnessing/cli.py ingest
python src/harnessing/cli.py stats
python src/harnessing/cli.py search "memory harness"
python src/harnessing/cli.py bundle "transcript ingestion" --limit 3
```

## Expected Result

- SQLite DB is created under `.harnessing/memory.db`
- ingestion succeeds
- search returns doc or memory hits
- bundle returns compact markdown context

