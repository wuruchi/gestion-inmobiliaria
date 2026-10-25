# ADR 0013: Missing entities

- Status: Accepted (migrations `0035` to `0037`)
- Revises: ADR 0001 (energy columns on `Inmueble`; `DatosInternos`).

## Decisions

- **`CertificadoEnergetico`**, one per listing, replaces `Inmueble.eficiencia`, `nombre_eficiencia`,
  `consumo_energetico`, `emisiones_co2` and the `certificado_energetico` type of `RegistroLegal`. It adds
  `fecha_emision` and `fecha_vencimiento`. `eficiencia` and `nombre_eficiencia` were the same fact (confirmed by the
  agency), so there is one rating, a letter `A` to `G`. The detail returns it as `certificado_energetico`
  (`null` without one); the four old top-level keys are gone, which breaks the API as accepted before.
- **`AcuerdoAdministracion`** (the agency's "Acuerdo de Administración") holds `fecha_firma`, `fecha_fin` and the three
  flags `exclusiva`, `gestion_comercial`, `administracion`. A listing can have several, so renewals keep a history.
  Overlapping agreements are not prevented. It is private.
- **`cat_nrc`** left `DatosInternos` as `Inmueble.referencia_catastral`, not as a `RegistroLegal` row as the TODO said:
  `RegistroLegal` is public and `cat_nrc` was private. It stays private because `Inmueble` is an allow-list.
- **`DatosInternos.fecha_tasacion`** dates the owner valuation; it needs an amount. No history table: the agency only
  needs to know how old the current value is.
- **`Propietario.nif`** is unique when set (empty may repeat). Migration `0037` stops and lists repeated NIFs
  before adding the constraint. The NIF is compared as typed, so `X1` and `x1` are different.
- **Audit columns** (`created_by/at`, `updated_by/at`) on `InmuebleModalidad` and `Condiciones` through the abstract
  `Auditoria`. The admin fills the users, also when an offer is saved from the listing's inline. `update()`, scripts
  and `bulk_create()` skip it. Existing rows get the migration time as `created_at` / `updated_at`. The API never
  returns them (`CondicionesSerializer` excludes them explicitly).
- **Parking `valor` and `renta`** stay internal notes outside the price model; the help text says so. The optional
  price of a space is still the only public parking price.

## Consequences

- Reversing `0035` writes the rating back to both old columns and recreates the registry rows; the dates are lost.
  Reversing `0036` keeps only the latest agreement per listing.
- Existing certificate ratings that are not a letter A-G are dropped to empty.
