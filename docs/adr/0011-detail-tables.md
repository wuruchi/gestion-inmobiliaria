# ADR 0011: detail tables: checks, unknown versus zero, `Distribucion`, split of `Otros`

- Status: Accepted (migrations `0031`, `0032`, `0033`)

## Context

The one-to-one detail tables had four problems: rules that lived only in people's heads, a missing row and a row of
zeros that meant the same, bathrooms in a separate two-column table, and `Otros`, a catch-all that mixed unrelated
concerns.

## Decisions

### Checks (`0031`)
Database constraints (with a message for `full_clean`): `Distribucion.exteriores <= dobles + individuales`,
`Inmueble.sup_util <= sup_construida`, and `fecha_baja >= fecha_alta`. The migration first stops with the list of
offending listings instead of failing on the constraint. A comparison with an unknown (empty) side is not checked.

### Unknown versus zero
A missing row in a detail table means the facts are not recorded (unknown). `n_habitaciones` and `n_banios` are
`null` in that case, no longer 0, so the `habitaciones` filter never matches an unknown listing. In `Distribucion` every
count is nullable: empty is unknown, 0 is confirmed none. This was needed because bedrooms and bathrooms now share a
row and one is often known without the other.

### `Distribucion` (`0032`)
`Banios` is merged into `Dormitorios`, and the table is renamed `Distribucion` (a table named "bedrooms" holding
bathrooms would repeat the catch-all problem). It has `dobles`, `individuales`, `exteriores`, `suites`, `banios`,
`capacidad_personas` and `suelo_banio`. The API has one `distribucion` section instead of `dormitorios` and `banios`.
`n_habitaciones` is the sum of the known counts, `null` if both are empty. Reversing the migration turns empty
counts into 0.

### Split of `Otros` (`0033`)
- `anio_ultima_reforma` goes to `Inmueble`, next to `anio_construccion`, with the same range check.
- (Revised by ADR 0020: the flags now live in `InclusionesAlquiler`, per rental offer.) `gastos_comunidad_incluidos` and `ibi_incluido` go to `Inmueble`, next to the amounts `gtos_comunidad` and `ibi`.
  The text `Condiciones.incluido` stays as the description of what a price includes.
- `capacidad_personas` goes to `Distribucion`.
- `acepta_animales` and the stay limits go to a new `TerminosAlquiler`, one optional record per rental offer, like
  `RegulacionAlquiler`. They were first planned for `Condiciones`, but that table is shared text keyed by name, and a
  listing-specific number would force a copy of it per listing. The offer is the right owner: a temporary and a habitual
  offer of the same dwelling have different limits. The record is `null` in the API for a sale or when nothing was
  recorded.
- What is left is renamed `Caracteristicas` (floor material, `exterior`, height, orientation flags, `chimenea`, views,
  facade).

## Consequences

- API: `otros`, `dormitorios` and `banios` are gone; `caracteristicas` and `distribucion` replace them, `terminos` is
  inside each rental entry of `modalidades`, and `anio_ultima_reforma` and the included flags are top-level. This breaks
  the old contract, accepted while the contract is being redesigned.
- The migration copies the terms to every monthly offer of the listing. A listing with terms but no rental offer loses
  them. Reversing keeps the terms of the first offer only.
- Existing data that breaks a check must be corrected before migrating.
