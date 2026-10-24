# Pending model tasks

Scope: the Django models in `backend/base/models/` and what depends on them.
Numbers match the improvement list from the model review (1 to 16).

## Done
- [x] 1. One source for each duplicated fact (equipment, stay limits, maximum people)
- [x] 2. `Modalidad` model (temporal, habitual, venta, otros) with several per listing
- [x] 3. Public detail output is an allow-list, with a test that classifies every column
- [x] 4. Indexes for the search filters, fewer queries on the list endpoints
- [x] Regulatory fields, balconies, energy consumption, `CondicionesAlquiler`, `SolicitudReserva`
- [x] `Barrio`, and the 73 Barcelona barrios in the seed tool
- [x] Detail tables exposed in the API, yes/no integers turned into booleans, typos renamed

## Data quality
- [ ] 5. Text that should be numbers
  - `Otros.estancia_minima` / `estancia_maxima` ("2 meses", "32 días") become integer months or days
  - `Otros.capacidad_personas` is already an integer; check nothing else stores people as text
- [ ] 6. Location stored twice
  - `Inmueble.poblacion`, `zona` and `zona_ref` duplicate the municipality, district and barrio links
  - Decide what stays (`codigo_postal`, street) and fill the rest from the links
- [ ] 7. Database rules
  - Prices and surfaces cannot be negative
  - A listing needs at least one `modalidad` (check in `clean()`, not a constraint)
  - Reference-index minimum/maximum check also as a database constraint
  - Venta listing needs `importe_venta`, rental listings need `importe_alquiler`
- [ ] 8. Types
  - `fecha_disponibilidad` is a date and time; it only needs a date
  - `sup_*` allows at most 999.99 m²; widen for offices and premises

## Structure
- [ ] 9. Merge small detail tables (for example `Salon`, `Terraza`, `Cocina`, `Carpinteria`) to cut joins
- [ ] 10. Photos (`ImageInmueble`)
  - `ImageField` instead of `FileField`
  - Explicit position column
  - Only one default photo per listing (constraint)
  - Alt text
- [ ] 11. `Propietario` model instead of free-text `propietario`
  - Move the private fields (`propietario`, `notas_internas`, `otros_datos`, `cat_nrc`, `valor_plz`, `renta_plz`, `fecha_firma`) out of `Inmueble`
- [ ] 12. Audit
  - `created_by` / `updated_by` (currently commented out)
  - Rent history beyond `ultima_renta`

## Naming and housekeeping
- [ ] 13. Naming
  - `n_banyos` vs `banios`, `original_Id`, `matterport_URI`
  - `modulo` as the name of the link to a listing in every detail table
  - `Transporte` uses `modulo_id` as its primary key, unlike the others
- [ ] 14. Fewer nullable columns: one empty state per field (blank for text, `default=False` for booleans)
- [ ] 15. Squash the 28 migrations into one before real data exists
- [ ] 16. Reservation requests
  - Status beyond the `atendida` flag
  - Retention rule for email and phone

## Open decisions from this review
- [ ] Deleting a `Modalidad` silently unlinks it from every listing; protect it if that is not wanted
- [ ] A listing with the "venta" modalidad can still carry only a rent price (see 7)
- [ ] `parking` flag was dropped; confirm `Otros.plazas_aparcamiento` is enough
- [ ] Keep `n_habitaciones` on `Inmueble`, or add a total to `Dormitorios`

## Data and setup that depend on the models
- [ ] Apply migrations to the local `db.sqlite3`, then run `python seed.py locations` and `python seed.py modalidades`
- [ ] Create the default "Condiciones de alquiler" record in the admin
- [ ] Districts and barrios for cities other than Barcelona (L'Hospitalet, Badalona, Terrassa) have no uniform official source yet
- [ ] Property importer (`import-inmuebles`) in `seed`
  - Quoted-TSV parser and `NULL` handling
  - Dry run, upsert on `referencia`
  - Match districts and barrios by slug
  - Skip the junk rows (`aulasbcn`, `NULL`)
  - Needs answers: is the sample export real client data, and is there a fuller export?

## Frontend follow-ups
- [ ] Detail page sections for the new data (kitchen, security, surroundings, transport, regulatory, conditions)
- [ ] Reservation request form posting to `/api/inmuebles/<id>/reservas/`
- [ ] Barrio and modalidad filters in the search
- [ ] Rebuild with `./publish.sh` (the compiled bundle still contains the old Heroku URL)
- [ ] Compile the frontend with the new types (`node_modules` is not installed, so it has not been type-checked)
