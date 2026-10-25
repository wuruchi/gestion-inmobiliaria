# ADR 0012: Remove derivable data

- Status: Accepted (migration `0034`)

## Context

Some columns stored what other columns already say, with constraints and `clean()` code to keep the copies in step.

## Decisions

- `InmuebleModalidad.mas_iva` is dropped. `tipo_iva` (0-100) is the source: set means the price excludes VAT,
  empty means VAT is included. `mas_iva` stays as a read-only property, so the API output does not change.
  The constraint `inmueble_modalidad_iva_coherente` becomes `inmueble_modalidad_iva_rango`.
- `PlazaAparcamiento.precio_opcional_mas_iva` gets the same treatment (`plaza_iva_rango`). The optional price
  keeps its own unit for now; tying it to the price model is left to the parking decision (`valor` / `renta`).
- `Inmueble.direccion_short` stays a stored column. It is a display override written by staff, not computed from
  `direccion`; the field help text says so.
- `Condiciones.modalidad` stays: it picks the default record per modalidad and says which fields apply.
  The model rejects conditions of another modalidad. The database cannot express it without a composite key, so
  `python manage.py comprobar_condiciones` lists offers that bypassed the model (`update()`, `bulk_create()`, SQL)
  and fails if there are any. This follows ADR 0006 (detect instead of enforce).

## Consequences

- A rate of 0 now means "excludes VAT, at 0 %"; it used to need the flag as well.
- Migration `0034` needs no data copy: the old constraint already guaranteed `mas_iva == (tipo_iva IS NOT NULL)`.
  Reversing it restores the flag from the rate.
