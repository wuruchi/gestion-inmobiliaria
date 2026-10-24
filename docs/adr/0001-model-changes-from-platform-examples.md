# ADR 0001: Model changes from the platform examples

- Status: Accepted (implemented; migrations `0002`–`0017`)
- Source: comparison of the saved ATBarcelona (rental) and idealista (sale) listings against `backend/base/models/`.
  Extracted from the completed `TODO.md` before it was deleted.

## Context

The listing models had to carry what real rental and sale pages show: legal registry numbers, VAT, sale-only
data, media types, request types and agency-private data. Only Barcelona is served, but nothing may assume a
single province or Catalan-only rules.

## Decisions

### Scope and legal
- Registry numbers (AICAT, cédula, energy certificate, tourist licence) live in `RegistroLegal`, one per type per
  listing (`otro` may repeat). They are public in the API.
- `ocultar_direccion` hides the address only: the API keeps the keys of `direccion`, `direccion_short` and
  `dir_descripcion` and returns empty strings. Coordinates stay public.
- `gran_tenedor` and `zona_tensionada` default to `False`.

### Existing fields
- `suites` is a subset of `dobles`/`individuales`, not extra rooms. The bedroom total is `dobles + individuales`.
- Stay limits are a value plus a unit (`dias`, `meses`, `anios`); min ≤ max is compared in days.
- Included-in-price flags (`gastos_comunidad_incluidos`, `ibi_incluido`) live together in `Otros`; `Inmueble`
  keeps only the amounts (`gtos_comunidad`, `ibi`).

### Pricing and offer
- Prices exist only in `InmuebleModalidad`. `precio` is the price as advertised; with VAT excluded it is the net
  price and `importe_*` in the API stay net.
- Conditions are per price (`InmuebleModalidad.condiciones`, same modalidad), not per listing. Each modalidad has
  at most one default record, used by the API when a price has none.
- `HistorialRenta` was replaced by `HistorialPrecio` (per modalidad). Seeded default conditions are created only
  when missing and never overwrite staff edits.
- Parking `valor` and `renta` stay private; the optional price is public.

### Sale data, media, requests, internal data
- `conservacion` (building condition) is not `estado` (availability). Only a `Vivienda` has a `subtipo`.
- Floor plans are `ImageInmueble` with `tipo='plano'`, served apart from photos, and can never be the default
  photo. Videos and tours are `MediaInmueble` links.
- `SolicitudReserva` keeps its name and the `/reservas/` endpoint; only admin and verbose names say "solicitud".
  `fecha_desde` is optional for every request type. The purge command also blanks `mensaje`.
- `DatosInternos` flags `exclusiva`, `gestion_comercial`, `administracion` are independent booleans. It is never
  serialized; a test covers list and detail.

### Testing
- Every public column is pinned by an allow-list test. One fixture per platform example (ATB-01..03,
  idealista-01..03) lives in backend tests only, each ending with a `NO MODELADO` note.

## Out of scope
- Sub-units inside one listing (a building with two duplexes stays one row).
- Visit/favourite/contact counters, agency profile pages, site-wide FAQs.
- A public tenant-audience filter; mortgage calculators.
- Seeding locations beyond Barcelona (load only when needed).

## Working rules
- Frontend is ignored until the backend work is done.
- The dev database is disposable: schema changes may skip data migrations.

## Consequences
Later normalization work (see `TODO.md`) may revise parts of this, notably where `gran_tenedor`, the VAT
columns, the current price and the rent-only regulatory columns live. Where it does, a new ADR supersedes the
relevant decision above.
