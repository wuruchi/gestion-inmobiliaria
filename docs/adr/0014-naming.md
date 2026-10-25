# ADR 0014: Naming consistency

- Status: Accepted (migrations `0038` to `0040`)

## Decisions

- **Counts** carry an `n_` prefix, like `n_habitaciones` and `n_plantas`: `Estancias.terraza` is now `n_terrazas` and
  `Estancias.balcones` is `n_balcones`. Areas keep the `_m2` suffix (`terraza_m2`, `balcones_m2`, `jardin_m2`) and flags
  stay bare (`jardin`). Migration `0038` is a pure rename.
- **`Inmueble.tipo`** codes are lowercase like every other choice list: `vivienda`, `oficina`, `local`, `parking`,
  `otro` (default `otro`), with the same labels. Migration `0039` maps the old values; any other value becomes `otro`.
  The `tipo=` filter of the API takes the new codes and rejects the old ones. `subtipo` still applies only to
  `vivienda`.
- **Primary key `id`.** `Inmueble`, `ImageInmueble`, `Provincia`, `Comarca`, `Municipio`, `Distrito` and `Barrio` named
  their key `_id`. The original reason was that `id` is a Python keyword; it is not. It is a built-in function, and an
  attribute or field named `id` shadows nothing (Django's own default key is `id`). Migration `0040` renames the
  field. The column type stays `AutoField`; moving to `BigAutoField` like the other tables is a separate change.

## Consequences

- API break (accepted): `_id` becomes `id` in every serializer and the detail/list keys, `tipo` values are lowercase,
  and the terrace/balcony counts are renamed. The `frontend/` still uses the old names.
- Every migration is reversible. The `RenameField` of the key was run forward and backward on SQLite with related
  rows; it has not been run on PostgreSQL.
