# seed

Populates the AtBarcelona database. It has its own Python runtime (3.13) and
requirements, and reuses the backend's models, so the schema lives in one place.

## Setup
```
cd seed
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Commands
```
python seed.py migrate              # apply the backend migrations
python seed.py locations            # province, comarcas, 311 municipios, Barcelona's 10 distritos and 73 barrios
python seed.py locations --dry-run  # report what would change, write nothing
python seed.py modalidades          # the four Modalidad rows: temporal, habitual, venta, otros
python seed.py modalidades --dry-run
python seed.py status               # row counts
python seed.py fetch-locations      # refresh data/*.json from the official sources
```
All commands except `fetch-locations` are safe to run repeatedly.

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

## Tests
```
python -m unittest discover -s tests
```
`data/modalidades.json` is application configuration maintained by hand, not downloaded.
