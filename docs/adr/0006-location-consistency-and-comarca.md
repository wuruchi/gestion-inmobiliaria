# ADR 0006: Locations keep three keys and are checked by a scan; a comarca has no province

- Status: Accepted (migration `0023`)
- Revises: ADR 0001 (location hierarchy as modelled).

## Context

A listing stores `municipio`, `distrito` and `barrio`, which are not independent: a barrio belongs to one distrito
and a distrito to one municipio. The model checks this on `save()`, but `bulk_create()`, `QuerySet.update()` and raw
SQL skip those checks, and the database cannot express the rule without composite foreign keys (not native in
Django, and awkward on SQLite). Research on Catalonia also showed that:
- districts and neighborhoods are defined by each city (only Barcelona's, nested, are confirmed and loaded);
- a comarca is not a child of a province: Cerdanya is split between Lleida and Girona.

## Decisions

- The listing keeps `municipio`, `distrito` and `barrio`. Consistency stays in `clean()` and `save()`, and is made
  detectable: `base.comprobaciones.inconsistencias_ubicacion()` and the read-only command
  `python manage.py comprobar_ubicaciones`, which lists offenders and fails when there are any. It also finds
  municipios whose code does not start with their province's.
- `Comarca.provincia` is removed. `Comarca.codigo` and `Comarca.slug` are unique on their own. The rule "the comarca
  must be in the municipio's province" is removed; the province is only on `Municipio`.
- The seed no longer reads or writes a province for comarcas, rejects a stale `provincia` key in the data file,
  accepts a comarca that groups municipios of several provinces, and runs the location scan after loading
  (`seed.py locations`, also `seed.py check-locations`, exit status 1 on problems).
- Migration `0023` is reversible: going back gives each comarca the province of its municipios.

## Not done

- A database guarantee for the hierarchy, and a unified sub-municipal table (`Zona`). Revisit when a second city's
  divisions are loaded and the real structure is known (open item in `TODO.md`).
- Entitats municipals descentralitzades and vegueries are not modelled.

## Addendum: `Zona` deferred (2026-10-25)

The two fixed sub-municipal levels (`distrito`, `barrio`) fit Barcelona, the only city with divisions loaded. Other cities
may have one level, a different count of levels, other names, or areas that cross district limits. A unified table
(`Zona(municipio, parent, nombre, nivel)`, a listing pointing at its most specific zone) would take any structure and make
the nesting problem disappear, since the parent chain is the nesting. It would also rewrite the locations, the listing,
the admin dropdowns, the API filters (`distrito`, `barrio`), the seed and many tests.

Decision: do nothing until a second city's divisions are loaded and the real structure is known; designing it now would
be guessing. If that city fits two levels, the current model stays. If not, the migration is mechanical: each distrito
becomes a zone with `nivel='distrito'`, and each barrio a zone with its distrito as parent.
