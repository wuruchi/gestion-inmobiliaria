# seed

Populates the AtBarcelona database with reference data: locations and modalidades. It has its own
Python runtime (3.13) and requirements, and reuses the [backend](../backend/README.md)'s models,
so the schema lives in one place.

## Setup
```
cd seed
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Typical first run
```
python seed.py migrate
python seed.py locations
python seed.py modalidades
python seed.py status
```

## Commands
```
python seed.py migrate              # apply the backend migrations
python seed.py locations            # province, comarcas, 311 municipios, Barcelona's 10 distritos and 73 barrios
python seed.py locations --dry-run  # report what would change, write nothing
python seed.py modalidades          # the three Modalidad rows: temporal, habitual, venta (with their price unit)
python seed.py modalidades --dry-run
python seed.py status               # row counts
python seed.py fetch-locations      # refresh data/*.json from the official sources
```
All commands except `fetch-locations` are safe to run repeatedly (they update existing rows).
`fetch-locations` rewrites `data/*.json` from the internet; review the diff before committing it.

## Configuration
- `ATB_BACKEND_PATH`: backend project (default `../backend`).
- Database: the same `DB_*` variables as the backend (Postgres when `DB_NAME` is set),
  otherwise SQLite at `<backend>/db.sqlite3`, or `DB_SQLITE_PATH`.
  Use the same values you use to run the backend.

## Data (`data/`)
Committed, so seeding works offline. Each file records its sources and retrieval date.
- Municipalities and comarcas: Generalitat de Catalunya open data, cross-checked with
  Idescat (`fetch-locations` aborts if the two disagree or the total is not 311).
  `codigo_ine` is the 5-digit INE code (the official 6th digit is a check digit).
- Distritos and barrios: Ajuntament de Barcelona open data (Barcelona city only).
- Modalidades (`data/modalidades.json`): application configuration maintained by hand, not downloaded.

## Tests
```
python -m unittest discover -s tests
```
The test migrates and seeds a temporary SQLite database, so it never touches your data.

## Not yet here
The property importer (loading listings from the old export) is planned; see [`../TODO.md`](../TODO.md).
