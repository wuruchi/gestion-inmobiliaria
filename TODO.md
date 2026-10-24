# TODO: normalization of the models

Source: database normalization review of `backend/base/models/` (section numbers like 1.2 refer to that review).
Earlier decisions are in `docs/adr/0001-model-changes-from-platform-examples.md`; where an item below revises one,
write a new ADR.

Every item that changes a column or an API field also needs: migration, admin, serializer allow-list, seed (if
reference data), tests, and an update of `MODELS.md`.

Rules: frontend is out of scope; the dev database is disposable, so data migrations may be skipped.

## Open decisions (settle before the item that depends on them)

- [ ] Current price: keep `InmuebleModalidad.precio` and append to `HistorialPrecio` on every change, or make
      the history the source and derive the current price? (1.4)
- [ ] Location: keep `municipio` + optional `barrio` and derive `distrito`, or keep the three FKs with a DB-level
      guarantee? (1.1)
- [ ] `estado` per listing or per modalidad? (4)
- [ ] Equipment catalogue (2.4): do it, or keep the wide typed tables? Default: keep, and only unify the
      count-vs-boolean convention.

## 1. Correctness: facts in the wrong place

- [ ] Move `gran_tenedor` from `Inmueble` to `Propietario`; expose it in the API only if needed. (1.2)
- [ ] Decide where `zona_tensionada` comes from (location plus date) and stop storing it per listing. (1.2)
- [ ] Single source of truth for the current price, per the decision above; remove the possible drift between
      `InmuebleModalidad.precio` and `HistorialPrecio`. (1.4)
- [ ] Rent-only regulatory columns (`ultima_renta`, `indice_referencia_min/max`, `actualizacion_renta`,
      `situacion_5_anios`) move to the rental offer (on or under `InmuebleModalidad`). (1.3)
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
- [ ] Location columns on `Inmueble` per the decision above; add a DB guarantee for the hierarchy. (1.1)
- [ ] Review `Municipio.provincia` / `Comarca.provincia` / `codigo_ine` prefix redundancy. (1.1)
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

- [ ] Co-ownership: `InmueblePropietario(inmueble, propietario, porcentaje)`; make `Propietario.nif` unique when
      set. (4)
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
