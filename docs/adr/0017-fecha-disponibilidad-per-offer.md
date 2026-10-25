# ADR 0017: `fecha_disponibilidad` belongs to each offer

- Status: Accepted (migration `0041`)
- Revises: ADR 0004 (which left the date on `Inmueble`).

## Context

A listing can be offered under several modalidades (rent now, sale, a temporary let). "Available from" differs between
them, and the state (`estado`) already lives on each offer. A single listing date made a date search by modalidad compare
the wrong date and could not say which offer it described.

## Decisions

- `InmuebleModalidad.fecha_disponibilidad` is a required date ("disponible desde"). Its default is today (a callable),
  so the admin pre-fills it; the database does not allow null.
- `Inmueble.fecha_disponibilidad` is no longer a column. It is a property: the earliest date among the offers that are
  not `cerrado`, or null when every offer is closed (or there are none). The API keeps the top-level key and adds the
  date to each `modalidades[]` entry.
- A closed offer affects nothing else: not the listing's date, not the list order, not a date search.
- The list is ordered by availability state, then by that derived date (an annotation; null last), then `id`.
- `fecha_entrada` selects listings that have an open (`disponible` or `reservado`) offer available on or before the
  date. With a modalidad in the URL, or a `max_precio`, it is the same offer that satisfies all of them. An invalid date
  returns 400 (it used to fail inside the query). A listing with no open offer is excluded when a date is given.
  Previously a listing with no date never matched; now every offer has one.
- The index `inm_web_fecha` is dropped with the column.
- Migration `0041`: each offer takes its listing's date, else the listing's `fecha_alta`, else the migration date.
  Reversing sets the listing's date to the earliest of its open offers (all offers if none is open).

## Consequences

- API break (accepted): `modalidades[]` gains `fecha_disponibilidad`, and the top-level value is derived and can be
  null for a fully closed listing.
- The migration cannot know the real date of an offer whose listing had none: those take a stand-in date that staff
  should review.
