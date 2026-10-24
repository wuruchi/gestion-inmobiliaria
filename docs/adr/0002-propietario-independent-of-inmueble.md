# ADR 0002: Propietario is independent of Inmueble

- Status: Accepted (migration `0019`)
- Revises: ADR 0001 (`gran_tenedor` default on `Inmueble`; `DatosInternos.propietario`).

## Context

`DatosInternos.propietario` allowed one owner per listing, and `gran_tenedor` was stored on each `Inmueble`.
Being a large holder is a fact about the owner, so two listings of the same owner could disagree, and
co-owned listings could not be recorded.

## Decisions

- `Propietario` does not depend on `Inmueble`. It can exist with no listing.
- A listing has many owners and an owner has many listings, through `InmueblePropietario`
  (`inmueble` CASCADE, `propietario` PROTECT, optional `porcentaje` above 0 and up to 100, one row per pair).
  The sum of shares is not constrained.
- `gran_tenedor` is a column of `Propietario` (default `False`). `Inmueble.gran_tenedor` and
  `DatosInternos.propietario` are removed.
- Requirement (confirmed): a listing must show that it is owned by a large holder (`gran propietario`).
- The public detail keeps the `gran_tenedor` key to meet that. It is derived:
  `true` when any owner of the listing is a large holder. Owners, their data and shares are never serialized.
- Migration `0019` copies each `DatosInternos.propietario` to a link and marks the owner as large holder if
  their listing was. It is reversible (back to the first owner of each listing).

## Consequences

- Listings with no owner show `gran_tenedor: false`.
- The detail view prefetches `propietarios` so the field costs one query however many owners there are.
