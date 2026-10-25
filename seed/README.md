# seed

Populates the AtBarcelona database with reference data: locations, modalidades, the default conditions of each modalidad and the main agency. It has its own
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
python seed.py agencia
python seed.py zonas-tensionadas
python seed.py status
```
To use the admin, create a user in the backend project: `cd ../backend && python manage.py createsuperuser`.

## Commands
```
python seed.py migrate              # apply the backend migrations (base, auth, admin, sessions)
python seed.py locations            # province, comarcas, 311 municipios, Barcelona's 10 distritos and 73 barrios
python seed.py locations --dry-run  # report what would change, write nothing
python seed.py modalidades          # the three Modalidad rows: temporal, habitual, venta (with their price unit)
python seed.py modalidades --dry-run
python seed.py condiciones         # the default Condiciones of each modalidad (needs modalidades first)
python seed.py condiciones --dry-run
python seed.py agencia             # the main agency: AtBarcelona (ATB), AICAT 5205 (never overwrites)
python seed.py agencia --dry-run
python seed.py zonas-tensionadas  # the stressed-zone declarations of the municipios already loaded (never overwrites)
python seed.py zonas-tensionadas --dry-run
python seed.py fake-offers --count 20   # development only: fake offers built from the saved example pages
python seed.py fake-offers --clean      # delete them again
python seed.py check-locations      # check that listings' municipio/distrito/barrio nest (read only; exit 1 if not)
python seed.py status               # row counts
python seed.py fetch-locations      # refresh data/*.json from the official sources
```

All commands except `fetch-locations` are safe to run repeatedly. `locations` and `modalidades` update existing rows;
`condiciones` only creates what is missing (see below).
`fetch-locations` rewrites `data/*.json` from the internet; review the diff before committing it.

## Location rules
`locations` checks the data files before it writes anything, and aborts with the full list of problems:
- a municipio's `codigo_ine` must start with the code of a province in `provincias.json`;
- its `comarca` must exist in `comarcas.json`. A comarca has no province (it may group municipios of several, as
  Cerdanya does), so a `provincia` key on a comarca is stale and reported;
- every distrito must point at a municipio in the files, and every barrio at a distrito in the files.

The backend models enforce the code-prefix rule on every save, so rows written by the seed and by the admin obey
one set of rules. After a real `locations` run the seed also runs the backend's location scan
(`comprobar_ubicaciones`) and exits with status 1, listing the offenders, if any listing's municipio, distrito and
barrio do not nest or a municipio code does not match its province. `check-locations` runs just that scan. Distritos and barrios are optional for a
listing: only Barcelona city has them loaded, so other municipios have a municipio-level location only.

## Fake offers (development only)
`python seed.py fake-offers` fills a development database with realistic listings, so the API and the frontend have
something to show. Never run it against real data. It needs the locations, modalidades, default conditions and the
agency to be loaded (the "Typical first run" above, plus `python seed.py zonas-tensionadas` for the rent-regulation data).

```
python seed.py fake-offers --count 30                      # 30 offers in Barcelona
python seed.py fake-offers --count 15 --municipio Sabadell # another municipio, by name or 5-digit INE code
python seed.py fake-offers --count 30 --seed 42            # repeatable (the seed is printed when not given)
python seed.py fake-offers --count 30 --dry-run            # build everything, roll it back, copy no files
python seed.py fake-offers --count 30 --no-media           # no photos or links
python seed.py fake-offers --clean                         # delete the fake offers and their owners
```
Options: `--examples PATH` (the folder with the saved example pages, default `../../gestion-inmobiliaria-examples`, or the
`ATB_EXAMPLES_PATH` variable) and `--prefix P` (references are `P-0001`; default `DEV`, and `--clean` only deletes that
prefix). Numbering continues after the last `DEV-NNNN` in the database. One run is one transaction.

How an offer is built:
- **One example per offer, in turn.** Offer `n` takes the structure of example `(n - 1) % 9`: atb-01, atb-02, atb-03,
  idealista-01, idealista-02, idealista-03, locb-01, locb-02, locb-03. That fixes the kind of property and offer (a
  furnished seasonal flat, an office, a terraced house for sale, a long-term rental...), the rooms, the equipment, the
  legal records and the stay terms, and it uses **all the photos and the video or tour of that example**, labelled
  by hand (`data/fake/medios.json`). So offer 3, 12, 21... shows atb-03's 33 photos and its Matterport tour.
- **What varies:** the place (a real street of a real barrio, with postal code and coordinates), the surface (±10 %),
  the floor, the year, the price (per m² by district, with noise), the state and dates of each offer, the owner (some own
  several listings, 10 % are shared, a few companies are large holders), the price history, the energy certificate, the
  cédula, the NRUA (some in process), the rent index and the previous rent of a rental in a stressed zone, the management
  agreement and the private notes. A rental sometimes also has a long-term offer and the other way round.
- **Text:** the title and the Spanish description of each example, with English and Catalan versions on some offers.
- **Houses stay out of the centre:** the two house examples are placed in Les Corts, Sarrià-Sant Gervasi, Horta-Guinardó,
  Nou Barris and Sant Andreu.
- **Other municipios** get generic Catalan street names around their centre and, if the database holds its districts, a
  district and barrio. Prices use a factor of Barcelona's (`data/fake/precios.json`).

The photos are copied once into `MEDIA_ROOT/seed-examples/<example>/` (the backend's media folder, `DJANGO_MEDIA_ROOT`
or `backend/media`) and every offer of that example points to the same files. They are third-party images with the
portals' watermarks: use them for development only and do not publish or commit them. The example pages are not part
of this repository.

Limits: the data is plausible, not true (street and number combinations, prices and indexes are approximations); the
rooms of an offer are those of its photos; `comprobar_regulacion_alquiler` flags the fake offices, because it does not
tell offices from homes.

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
- Stressed zones (`data/zonas_tensionadas.json`): declarations TER/800/2024 (140 municipios) and TER/2408/2024
  (131) from the Generalitat's list, with municipality names as printed there. The command matches them to the
  municipios in the database; those whose province is not loaded (112 today, outside Barcelona province) are listed
  as "not loaded" and picked up by a later run. Existing declarations are kept as staff left them. The 140's start
  date is assumed, and the 2026 changes are not loaded (see ADR 0015). Every loaded municipio of Catalonia is also
  marked `declaraciones_cargadas`: the list covers all of Catalonia, so a municipio not on it is known not to be stressed.
  Municipios elsewhere stay unmarked and report `zona_tensionada: null` (ADR 0019).
- Agency (`data/agencia.json`): AtBarcelona (ATB), AICAT 5205, with the contact data of its listing pages; the API number is
  empty because the pages do not publish it. An existing agency is kept as staff left it.
- Modalidades (`data/modalidades.json`): application configuration maintained by hand, not downloaded.
- Fake offers (`data/fake/`): streets, postal codes and metro stations of Barcelona's barrios, price levels, names, and the
  photo labels of the examples, all written by hand and approximate (see above).
- Conditions (`data/condiciones.json`): one default `Condiciones` per modalidad, written by hand from the
  AT Barcelona (rent: deposit, fees, ITP, utilities, final cleaning, tenant documents) and idealista (sale: ITP,
  notary, registry, gestoría) listings. Review the legal wording and the tax rates before publishing.

## Default conditions
`condiciones` creates `Alquiler de temporada`, `Alquiler de vivienda habitual` and `Compraventa`, each the default
of its modalidad. Staff edit them in the admin, so the command never overwrites: it skips a record whose name
exists, or whose modalidad already has a default, and reports `kept`. It stops if the modalidades are not loaded.
The rent defaults include the rent-update clause (`actualizacion_renta`, the IRAV, which applies only if agreed). Because the command never overwrites, default records created before that field existed keep it empty: set it in the admin.

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
