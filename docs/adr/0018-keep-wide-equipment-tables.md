# ADR 0018: Keep the wide equipment tables

- Status: Accepted

## Context

Equipment and features live in one-to-one tables of typed columns: `Dotacion` (23 items), `Instalaciones` (14),
`Seguridad` (11), `OtrosEspacios` (10), `AreaRecreo` (6) and `Entorno` (15), roughly 80 items. The alternative was a
catalogue: `Equipamiento(codigo, nombre, grupo)` plus `InmuebleEquipamiento(inmueble, equipamiento, cantidad)`, so
staff could add items without a developer.

## Decision

Keep the wide tables. The convention for a count or a flag is ADR 0010, and an absent row means unknown (ADR 0011).

Reasons:

- The typed columns carry their own rules: counts, an area only when the item exists (`Entorno.jardin_m2`), and the
  unknown-versus-zero rule. A catalogue would have to rebuild all of it.
- Filters stay plain columns (`dotacion__lavadora=True`); a catalogue needs one join per filter.
- The API keeps a flat, documented object per group; with a catalogue the consumer has to know the item codes.
- The equipment list changes rarely, so the cost of a new item (a column, a migration, the serializer, the admin and
  the tests) is small, and nothing in the project says staff need to add items themselves.
- A catalogue means rewriting six tables, their serializers, admin, tests and fixtures, plus a data migration.

## Consequences

- Adding an item needs a developer.
- If staff later need items of their own, the cheap path is not a rewrite: keep the typed columns for the common items
  and add one table of extras (listing, name, optional count) for the rest. That is not built; add it only when someone
  asks for it.
