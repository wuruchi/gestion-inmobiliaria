# TODO: normalization of the models

Source: database normalization review of `backend/base/models/` (section numbers like 1.2 refer to that review).
Earlier decisions are in `docs/adr/0001-model-changes-from-platform-examples.md`; where an item below revises one,
write a new ADR.

Every item that changes a column or an API field also needs: migration, admin, serializer allow-list, seed (if
reference data), tests, and an update of `MODELS.md`.

Rules: frontend is out of scope; the dev database is disposable, so data migrations may be skipped.

Tests: never disable the suite. Start each group from a green run and update fixtures and tests in the same
commit as the model change. If a group breaks a whole example, skip only that test with
`@unittest.skip("TODO <item>")` and remove the skip when the group lands. A group is not done while the
suite is red or has a skip.

## Open decisions (settle before the item that depends on them)

- [x] Current price: `InmuebleModalidad.precio` stays the source and every change is appended to
      `HistorialPrecio` automatically; `ultima_renta` is derived from the history per modalidad (ADR 0005). (1.4)
- [x] Location: keep the three keys and detect violations instead of enforcing them in the database (ADR 0006). (1.1)
- [x] `estado` per modalidad: stored on `InmuebleModalidad`, derived for the listing (ADR 0004). (4)
- [ ] `fecha_disponibilidad` is per listing but "available from" depends on the offer; move it to
      `InmuebleModalidad` too? (4)
- [ ] Equipment catalogue (2.4): do it, or keep the wide typed tables? Default: keep, and only unify the
      count-vs-boolean convention.

## 1. Correctness: facts in the wrong place

- [x] `Propietario` is independent; a listing has many owners (`InmueblePropietario`) and `gran_tenedor` lives on
      `Propietario`. The detail still returns `gran_tenedor`, derived from the owners (ADR 0002). (1.2, 5)
- [x] `zona_tensionada` is derived from dated declarations per municipality (`DeclaracionZonaTensionada`, ADR 0003). (1.2)
- [ ] Load the real declarations (list, dates and resolutions) once verified with the Generalitat / DOGC. (1.2)
- [x] The history can no longer fall behind the current price (ADR 0005). (1.4)
- [x] Rent regulation data (index range, last-rent status/amount/end date) lives in `RegulacionAlquiler`, one per
      rental offer; `actualizacion_renta` moved to `Condiciones`; `situacion_5_anios` replaced by `renta_previa`
      (ADR 0007). (1.3)
- [x] `comprobar_regulacion_alquiler` lists habitual rentals in stressed zones with missing regulation data (ADR 0007).
- [ ] Decide whether to run the location and rent-regulation scans on a schedule or before publishing.
- [ ] Verify the exact legal scope (habitual vs temporary leases, contract dates) against the texts of Decret llei
      1/2025 and Llei 12/2023 before relying on `comprobar_regulacion_alquiler`.
- [ ] Move `Otros.estancia_*` and `acepta_animales` to the rental conditions. (3)
- [ ] `CertificadoEnergetico` table: `eficiencia`, `nombre_eficiencia`, `consumo_energetico`, `emisiones_co2`
      and the certificate number from `RegistroLegal`; check whether `eficiencia` and `nombre_eficiencia` are the
      same fact. (1.8)
- [ ] Group community fees and IBI (amount, included flag, text in `Condiciones.incluido`) under one owner. (1.9)

## 2. Remove derivable data

- [ ] Drop `InmuebleModalidad.mas_iva`; keep `tipo_iva` and expose `mas_iva` as a property. Update the
      constraint and the API. (1.5)
- [ ] Same for `PlazaAparcamiento.precio_opcional_*`; drop `precio_opcional_unidad` and tie the optional price
      to a modalidad. (1.5, 1.6)
- [x] Location columns stay as three keys; consistency is checked in the models and by `comprobar_ubicaciones`
      (ADR 0006). (1.1)
- [x] `Comarca.provincia` dropped: a comarca can span provinces (ADR 0006). (1.1)
- [ ] Revisit a unified sub-municipal table (`Zona`) when a second city's districts / barrios are loaded. (1.1)
- [ ] Decide whether `direccion_short` is computed or a documented display override. (1.10)
- [ ] DB-level check that `Condiciones.modalidad` equals `InmuebleModalidad.modalidad` (composite FK via
      `RunSQL`, or document `clean()` as the only guard). (1.7)

## 3. Repeating groups

- [ ] `Transporte` to one row per mode: `TransporteInmueble(inmueble, tipo, descripcion)`. (2.1)
- [ ] `Instalaciones`: `Suministro(inmueble, tipo, contador, compania, tipo_suministro)` for water, electricity
      and gas; heating type/subtype as choices. (2.2)
- [ ] `descripcion_es/en/cat` to `DescripcionInmueble(inmueble, idioma, texto)`; the API keeps flattening. (2.3)
- [ ] Free text with a closed domain to choices or lookups: `orientacion`, `tipo_fachada`, `office`, the three
      floor fields, `tipo_cocina`, `tipo_gas`, `situacion_actual`, `situacion_5_anios`, `usos`. (2.5)
- [ ] One convention for count vs boolean in `Dotacion`, `Estancias`, `OtrosEspacios`. (2.4)

## 4. Detail tables

- [ ] Merge `Banios` into `Dormitorios` (or one "distribution" table). (3)
- [ ] Split what is left of `Otros` by concern; move `anio_ultima_reforma` next to `anio_construccion`. (3)
- [ ] Define the meaning of a missing row versus a row of zeros; consider null for "unknown". (3)
- [ ] Add checks: `exteriores <= dobles + individuales`, `sup_util <= sup_construida`,
      `fecha_baja >= fecha_alta`. (3)

## 5. Missing entities

- [x] Co-ownership: `InmueblePropietario(inmueble, propietario, porcentaje)` (ADR 0002).
- [ ] Make `Propietario.nif` unique when set. (4)
- [ ] `DatosInternos`: move `cat_nrc` to `RegistroLegal`; extract the management agreement (`fecha_firma`,
      `exclusiva`, `gestion_comercial`, `administracion`) into its own model with dates. (4)
- [ ] Date the owner valuation (`tasacion_propietario`) or keep a history. (4)
- [ ] Audit columns (`created_by/at`, `updated_by/at`) on `InmuebleModalidad` and `Condiciones`. (4)
- [ ] Parking: decide whether `PlazaAparcamiento.valor` / `renta` fit the price model. (4)

## 6. Naming consistency

- [ ] Replace the `_id` primary key on `Inmueble`, `ImageInmueble` and the location models with `id`; check
      every `inmueble_id`, serializer and test that relies on it. (5)
- [ ] `Inmueble.TIPOS` values to lowercase snake_case like the other choice lists. (5)
- [ ] Rename `Banios.banios` and unify count-vs-area naming (`terraza` vs `terraza_m2`). (5)

## 7. Cross-cutting (after each group lands)

- [ ] Update `MODELS.md` and the ER diagram.
- [ ] Update `seed/` and its tests for any changed reference data.
- [ ] Re-pin the public API with the allow-list tests; the fixtures in `backend/base/tests_ejemplos.py` must
      still load.
- [ ] Write an ADR for each decision that revises ADR 0001.
