# seed

Populates the AtBarcelona database with reference data: locations, modalidades and the default conditions of each modalidad. It has its own
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
python seed.py condiciones
python seed.py status
```

## Commands
```
python seed.py migrate              # apply the backend migrations
python seed.py locations            # province, comarcas, 311 municipios, Barcelona's 10 distritos and 73 barrios
python seed.py locations --dry-run  # report what would change, write nothing
python seed.py modalidades          # the three Modalidad rows: temporal, habitual, venta (with their price unit)
python seed.py modalidades --dry-run
python seed.py condiciones         # the default Condiciones of each modalidad (needs modalidades first)
python seed.py condiciones --dry-run
python seed.py status               # row counts
python seed.py fetch-locations      # refresh data/*.json from the official sources
```
`python seed.py migrate` stops, listing the offenders, if an existing listing has no municipio or a location
that does not nest (migration `0002`); fix those rows first.

All commands except `fetch-locations` are safe to run repeatedly. `locations` and `modalidades` update existing rows;
`condiciones` only creates what is missing (see below).
`fetch-locations` rewrites `data/*.json` from the internet; review the diff before committing it.

## Location rules
`locations` checks the data files before it writes anything, and aborts with the full list of problems:
- a municipio's `codigo_ine` must start with the code of a province in `provincias.json`;
- its `comarca` must exist in `comarcas.json` and be in the same province (a comarca may carry an optional
  `provincia` key; without it, it is Barcelona's);
- every distrito must point at a municipio in the files, and every barrio at a distrito in the files.

The backend models enforce the same rules on every save (`Municipio`: code prefix and comarca province), so
rows written by the seed and by the admin obey one set of rules. Distritos and barrios are optional for a
listing: only Barcelona city has them loaded, so other municipios have a municipio-level location only.

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
- Conditions (`data/condiciones.json`): one default `Condiciones` per modalidad, written by hand from the
  AT Barcelona (rent: deposit, fees, ITP, utilities, final cleaning, tenant documents) and idealista (sale: ITP,
  notary, registry, gestoría) listings. Review the legal wording and the tax rates before publishing.

## Default conditions
`condiciones` creates `Alquiler de temporada`, `Alquiler de vivienda habitual` and `Compraventa`, each the default
of its modalidad. Staff edit them in the admin, so the command never overwrites: it skips a record whose name
exists, or whose modalidad already has a default, and reports `kept`. It stops if the modalidades are not loaded.

## Tests
```
python -m unittest discover -s tests
```
The tests migrate and seed a temporary SQLite database, so they never touch your data. They check the
committed data files nest properly, that broken nesting is reported, and that seeding twice changes nothing.

## Not yet here
- The property importer (loading listings from the old export), with a dry run and upsert on `referencia`.
  It will create `InmuebleModalidad` and `PlazaAparcamiento` rows and match distritos and barrios by slug.
- Distritos and barrios for cities other than Barcelona (L'Hospitalet, Badalona, Terrassa): there is no
  uniform official source yet.
