# ADR 0008: repeating groups become rows

- Status: Accepted (migrations `0025`, `0026`, `0027`)

## Context

Three places repeated the same columns once per member of a list: `Transporte` (a flag and a description per
mode), `Instalaciones` (meter and company for water, electricity and gas) and `Inmueble.descripcion_es/en/cat`
(one column per language). Adding a member (a transport mode, a language) needed a schema change, and any rule had
to be written once per copy.

## Decisions

- `TransporteInmueble(inmueble, tipo, descripcion)`: one row per mode, `tipo` from a list, unique per
  `(inmueble, tipo)`. A missing row means no such transport nearby, so the per-mode flag is gone.
- `Suministro(inmueble, tipo, contador, compania, tipo_suministro)`: one row per supply (agua, electricidad, gas),
  unique per `(inmueble, tipo)`. `tipo_suministro` is the gas type (natural, butano, propano, otro) and a
  constraint allows it only for gas. The old `gas` flag is derived (a gas row exists), which also removes its overlap
  with `contador_gas`.
- `Instalaciones` keeps the other columns. `tipo_calefaccion` (central, individual) and `subtipo_calefaccion`
  (gas_natural, electrica, gasoleo, biomasa, aerotermia, otro) are now choices.
- `DescripcionInmueble(inmueble, idioma, texto)`: one row per language (`es`, `en`, `ca`), unique per
  `(inmueble, idioma)`. The `Inmueble.descripcion_*` columns are not kept, not even as properties, so a new
  language touches no code.
- The API breaks on the descriptions (the contract is being redesigned anyway): `descripciones` is an object
  `{es, en, ca}` with only the languages that exist, in the list and the detail. `instalaciones` still has
  `contador_*`, `compania_*`, `gas` and `tipo_gas`; `transporte` still has `cerca_*` and `descripcion_*` per mode.
  Differences: `transporte` has no `id` or `inmueble` key, `instalaciones` and `transporte` are `null` when there is
  nothing to show, and heating and gas types are now the choice values (`central`, `gas_natural`, `natural`...)
  instead of free text.
- Migrations copy the data and are reversible. Free text that matches no choice becomes `otro`.

## Consequences

- A new transport mode or language is a new choice value, not a migration of columns.
- The list and the detail prefetch `descripciones` and `suministros` (and `transportes` in the detail); the list
  query count stays constant in the page size.
- A listing with supplies but no `Instalaciones` row still shows `instalaciones`.
- A later change could expose the rows as arrays instead of flattening; that is a breaking API change for the
  frontend, so it is left for when the frontend is revised.
