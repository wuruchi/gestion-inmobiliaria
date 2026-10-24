# ADR 0004: Availability (`estado`) belongs to each offer

- Status: Accepted (migration `0021`)
- Revises: ADR 0001 (`estado` as a column on `Inmueble`).

## Context

A listing can be offered under several modalidades. One `estado` column could not say that a flat is let but still
for sale, or that only the sale is reserved. "Alquilado" meant nothing for a sale-only listing and there was no
"Vendido".

## Decisions

- `InmuebleModalidad.estado`: `disponible` (default), `reservado`, `cerrado` (rented or sold). The meaning of
  closed follows the modalidad's price unit.
- `Inmueble.estado` is no longer a column. It is a property derived from the offers (rules in `MODELS.md`) and
  the list and detail keep returning `estado`, with the values `Disponible`, `Reservado`, `Alquilado` and the
  new `Vendido`.
- The list is ordered by an annotated rank (available, reserved, closed) then `fecha_disponibilidad`. The old
  `-estado` ordered the text descending, which put `Reservado` before `Disponible`; this is changed on purpose.
- The index `inm_web_estado_fecha` becomes `inm_web_fecha` (`publicar_web`, `fecha_disponibilidad`).
- Migration `0021`: `Reservado` reserves every offer; `Alquilado` closes the monthly offers (all of them when
  there are none). It is reversible, but a listing that is let and still for sale returns as `Disponible`.

## Consequences

- Staff set the state on each price in the admin; the admin list shows the derived state and can filter by offer state.
- `fecha_disponibilidad` stays on `Inmueble` for now (open item in `TODO.md`).
