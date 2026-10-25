# ADR 0015: Seed the stressed-zone declarations

- Status: Accepted

## Context

`DeclaracionZonaTensionada` (ADR 0003) was empty, so `zona_tensionada` was false everywhere and
`comprobar_regulacion_alquiler` flagged nothing. A declaration covers a whole municipality: the Generalitat's
resolutions and lists name municipalities only, never districts or barrios.

## Decisions

- `python seed.py zonas-tensionadas` loads `seed/data/zonas_tensionadas.json`: TER/800/2024 (140 municipios, DOGC
  9122 of 14 Mar 2024) and TER/2408/2024 (131 municipios, DOGC of 3 Jul 2024), from the Generalitat's published list.
- Municipalities are matched by name (the list prints the article last: "Bisbal d'Empordà, la"). A name that matches no
  municipio is reported as "not loaded", not an error: the location seed only holds Barcelona province, so 159 of the
  271 load today. Loading more provinces and re-running picks up the rest. A name matching two municipios aborts.
- It creates what is missing and never overwrites: a declaration with the same municipio and start date is kept as staff
  left it. It does not delete the placeholder rows migration `0020` may have created.
- Start dates are the first day of effect, which the state law sets as the day after the BOE publication:
  2024-10-10 for TER/2408/2024 (BOE 9 Oct 2024, per the ACM note) and 2024-03-16 for TER/800/2024 (BOE 15 Mar 2024).
  The second is assumed and not confirmed against the BOE text; the file says so.
- `hasta` is empty. A declaration lasts three years and is extended yearly, but the exact end dates were not found.

## Not loaded

TER/3739/2026 (DOGC 9775, 19 Oct 2026) extends the 140's zone in 118 municipios, so 22 leave; TER/3740/2026 declares 53
new ones, pending the BOE. Their dates and the names of the 22 are not confirmed yet.

## Consequences

- Until the 2026 changes are loaded, the 22 leaving municipios still show as stressed and the 53 new ones do not.
- Every number in the file comes from the Generalitat's pages; review it before relying on it legally.
