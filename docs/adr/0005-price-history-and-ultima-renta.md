# ADR 0005: Price history is written automatically; `ultima_renta` is derived from it

- Status: Accepted (migration `0022`)
- Revises: ADR 0001 (`ultima_renta` as a column on `Inmueble`; `HistorialPrecio` as hand-entered log).

## Context

The current price (`InmuebleModalidad.precio`) and its history (`HistorialPrecio`) were two copies that nothing kept
in step, and `Inmueble.ultima_renta` was a third, unrelated figure that depends on the modalidad.

## Decisions

- `InmuebleModalidad.precio` stays the source of the current price. `InmuebleModalidad.save()` appends
  a `HistorialPrecio` row dated today when the price is created or changes, so the latest row equals the current
  price. A second change on the same day replaces that day's row (a correction, not a new price). Saving without
  a price change adds nothing. Rows can still be entered by hand.
- `QuerySet.update()` and `bulk_create()` skip `save()` and so skip the history. Price changes must go through
  `save()`; this is documented, not enforced by the database.
- `Inmueble.ultima_renta` is removed. Each monthly offer exposes `ultima_renta` in the detail: the price charged
  before the one in force today, for that modalidad (future-dated rows ignored). It is `null` without an earlier
  price and for sale. The history itself stays private.
- Because history rows refer to the modalidad (`PROTECT`), a modalidad with price history cannot be deleted.
- The detail view prefetches the history, so the field costs one query however long the history is.
- Migration `0022` makes the latest history row equal each current price (dated on the migration day) and turns a
  listing's `ultima_renta` into an earlier history row of its monthly offers, only when that offer had no earlier
  row. It is reversible (back to the first monthly offer's previous price).

## Consequences

- The legal "last rent" is only as good as the history: it must hold the rent actually charged, not asking prices.
  The previous price is an approximation of the previous contract's rent.
- `ultima_renta` moved from the top level of the detail to each `modalidades` entry (API change).
