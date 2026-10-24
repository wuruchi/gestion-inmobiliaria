# Pending model tasks

Scope: the Django models in `backend/base/models/` and what depends on them.
Numbers 1 to 16 match the improvement list from the model review; 17 onward were added afterwards.
Rule of thumb: a value that can be derived from other rows is a computed property, not a stored column.

## Done
- [x] 1. One source for each duplicated fact (equipment, stay limits, maximum people)
- [x] 2. `Modalidad` model (temporal, habitual, venta) with several per listing
- [x] 3. Public detail output is an allow-list, with a test that classifies every column
- [x] 4. Indexes for the search filters, fewer queries on the list endpoints
- [x] Regulatory fields, balconies, energy consumption, `CondicionesAlquiler`, `SolicitudReserva`
- [x] `Barrio`, and the 73 Barcelona barrios in the seed tool
- [x] Detail tables exposed in the API, yes/no integers turned into booleans, typos renamed

## Data quality (done)
- [x] 5. Text that should be numbers: `Otros.estancia_minima_meses` / `estancia_maxima_meses` (months), `Entorno.distancia_playa_m` / `distancia_poblacion_m` / `distancia_ciudad_m` (metres), `Otros.altura_real_m` (metres). The migration converts what it can read ("2 meses", "1,5 km", "2,70") and stops, listing the values, on anything it would have to guess (bare distances, "32 días")
- [x] 6. Location stored once: `poblacion`, `ubicacion`, `zona`, `zona_ref` removed; the API's `zona` (barrio, else district) and `zona_ref` (district) are computed. The migration stops if a listing has that text but no municipio / distrito link. `direccion`, `direccion_short`, `dir_descripcion` and `codigo_postal` stay
- [x] 7. Database rules: prices, surfaces and energy use cannot be negative (validator + `CheckConstraint`), detail-table counts are `PositiveIntegerField`, reference-index min <= max is a `CheckConstraint`. The at-least-one-modalidad rule lives in the admin inline; the venta / rent price rule is item 17. Left: enforce the modalidad rule in any future write API
- [x] 8. Types: `fecha_disponibilidad`, `fecha_alta`, `fecha_baja`, `fecha_entrega` are dates; `sup_construida`, `sup_cont_comun`, `sup_util` allow up to 999,999.99 m²

## Structure (done)
- [x] 9. Merged `Salon`, `Terraza`, `Cocina` and `Carpinteria` into `Estancias` with a single `descripcion`; the API keeps the four nested keys
- [x] 10. Photos: `ImageField`, `posicion`, `alt_text` (renamed from `label`), one default photo per listing, required link, redundant `unique_together` dropped
- [x] 11. `Propietario` model; `DatosInternos` (one per listing) holds the owner link, `notas_internas`, `otros_datos`, `cat_nrc`, `fecha_firma`. `fecha_entrega`, `situacion_actual` and `cedula` stay on `Inmueble` (review later)
- [x] 12. Audit: `created_by` / `updated_by` set by the admin; `HistorialRenta` (private). `ultima_renta` stays a stored, public field

## Naming and housekeeping (done)
- [x] 13. Naming: every link to a listing is `inmueble` (was `modulo`; the API key changes with it); `original_id`, `matterport_url`, `n_banios` (API), `cristales_blindados`; `Transporte` has its own `id` like the other detail tables
- [x] 14. One empty state per field: text columns are `blank=True, default=''` (no NULL), booleans are never null, `sup_*`, `ibi`, `gtos_comunidad`, `geo_*` are optional in forms too. Numbers and dates that can be unknown stay nullable (unknown is not 0)
- [x] 15. The migrations are squashed into one `0001_initial` (no real data existed). The old files are not kept in the repo; `backend/db.sqlite3` was rebuilt from it and seeded (the previous file is `backend/db.sqlite3.bak`, ignored by git)
- [x] 16. Reservation requests: `estado` (pendiente, contactada, cerrada, descartada) replaces `atendida`; `python manage.py purgar_solicitudes [--meses 12] [--dry-run]` blanks name, email and phone on older requests and keeps the row. Left: run it on a schedule (cron) once deployed

## Pricing, parking and computed values
- [x] 17. Price per modalidad (`InmuebleModalidad`)
  - Required, non-negative `precio` per (listing, modalidad), unique; `Modalidad` link is `PROTECT`; `Modalidad.unidad_precio` (Monthly or Total) set by the seed tool
  - The `otros` modalidad is removed (3 modalidades left); `importe_alquiler` and `importe_venta` columns are gone, migrated into the new rows (the migration stops if a linked modalidad has no price)
  - Admin: inline on `Inmueble` that needs at least one modalidad with a price
  - API: `modalidades` is `[{codigo, nombre, unidad_precio, precio}]`; `importe_alquiler` (lowest monthly price) and `importe_venta` stay as derived fields so the frontend keeps working. `max_precio` compares that modalidad's price (monthly prices on `inmuebles/`)
  - Left: the frontend still reads `importe_*`; switch it to `modalidades[].precio` and show the unit (frontend follow-ups)
- [x] 18. `PlazaAparcamiento` model (many per listing)
  - Fields: `inmueble` (`CASCADE`), `numero` (unique per listing when given), `tipo` (coche or moto), `superficie`, `valor`, `renta`, `notas`; amounts cannot be negative
  - Removed `n_plz_garaje`, `sup_parking`, `valor_plz`, `renta_plz` from `Inmueble` and `Otros.plazas_aparcamiento`; the migration creates one plaza per counted space (it stops if a listing has several spaces and one set of figures)
  - `n_plz_garaje` is computed (count of plazas) and still returned by the detail endpoint; `plazas` is returned too (public: `numero`, `tipo`, `superficie`, `notas`). `valor` and `renta` stay private, as `valor_plz` and `renta_plz` were
  - A `tipo='Parking'` listing may also have plazas (optional, not hidden in the admin)
- [x] 19. Computed `n_habitaciones`
  - The stored column is gone; `Inmueble.n_habitaciones` is a property: `dobles + individuales + suites` of `Dormitorios` (`exteriores` left out), 0 without a `Dormitorios` row
  - List and detail still return `n_habitaciones`. The `habitaciones` filter runs in SQL on an annotation (`Inmueble.objects.con_habitaciones()`), with no extra queries
  - The migration stops, listing the offenders, if a stored number differs from the dormitorios total

## Decisions taken from this review
- [x] Deleting a `Modalidad` must not unlink it silently: `PROTECT` on the link, see 17
- [x] A listing with the "venta" modalidad needs a sale price: the price is required on the modalidad link, see 17
- [x] Parking gets its own model, see 18 (the dropped `parking` flag and `Otros.plazas_aparcamiento` are not enough)
- [x] Derived values are computed properties, not stored columns: `n_habitaciones` (19) and `n_plz_garaje` (18)

## Data and setup that depend on the models
- [x] Migrations applied to the local `db.sqlite3` and `python seed.py locations` / `modalidades` run (re-create your admin user with `createsuperuser`)
- [ ] Create the default "Condiciones de alquiler" record in the admin
- [ ] Districts and barrios for cities other than Barcelona (L'Hospitalet, Badalona, Terrassa) have no uniform official source yet
- [ ] Property importer (`import-inmuebles`) in `seed`
  - Quoted-TSV parser and `NULL` handling
  - Dry run, upsert on `referencia`
  - Match districts and barrios by slug
  - Skip the junk rows (`aulasbcn`, `NULL`)
  - Create `InmuebleModalidad` rows (with prices) and `PlazaAparcamiento` rows instead of the old price and parking columns (17, 18)
  - Needs answers: is the sample export real client data, and is there a fuller export?

## Frontend follow-ups
- [ ] Detail page sections for the new data (kitchen, security, surroundings, transport, regulatory, conditions)
- [ ] Reservation request form posting to `/api/inmuebles/<id>/reservas/`
- [ ] Show the price and unit of each modalidad on the list and detail pages, reading `modalidades[].precio` instead of `importe_*` (17)
- [ ] Barrio and modalidad filters in the search
- [ ] Rebuild with `./publish.sh` (the compiled bundle still contains the old Heroku URL)
- [ ] Compile the frontend with the new types (`node_modules` is not installed, so it has not been type-checked)
