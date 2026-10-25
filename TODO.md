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
- [x] `fecha_disponibilidad` moved to each offer; the listing shows the earliest date among its open offers
      (ADR 0017). (4)
- [x] Equipment catalogue (2.4): the wide typed tables stay; the count-vs-boolean convention was unified (ADR 0010,
      ADR 0018).

## 1. Correctness: facts in the wrong place

- [x] `Propietario` is independent; a listing has many owners (`InmueblePropietario`) and `gran_tenedor` lives on
      `Propietario`. The detail still returns `gran_tenedor`, derived from the owners (ADR 0002). (1.2, 5)
- [x] `zona_tensionada` is derived from dated declarations per municipality (`DeclaracionZonaTensionada`, ADR 0003). (1.2)
- [x] Declarations TER/800/2024 (140) and TER/2408/2024 (131) are seeded for the municipios loaded, 159 of 271
      (`python seed.py zonas-tensionadas`, ADR 0015). (1.2)
- [ ] Confirm the start date of TER/800/2024 (16 Mar 2024 assumed) against the BOE text of 15 Mar 2024. (1.2)
- [ ] Seed the other 112 municipios (Girona, Lleida, Tarragona) by loading those provinces, then re-run the command. (1.2)
- [ ] Load the 2026 changes once the BOE publishes them and the dates are known: TER/3739/2026 extends 118 of the
      140, so the other 22 need an end date; TER/3740/2026 adds 53. (1.2)
- [ ] Review the placeholder declarations that migration `0020` created in an existing database (start date = the
      migration date) and delete or correct them. (1.2)
- [x] The history can no longer fall behind the current price (ADR 0005). (1.4)
- [x] Rent regulation data (index range, last-rent status/amount/end date) lives in `RegulacionAlquiler`, one per
      rental offer; `actualizacion_renta` moved to `Condiciones`; `situacion_5_anios` replaced by `renta_previa`
      (ADR 0007). (1.3)
- [x] `comprobar_regulacion_alquiler` lists habitual rentals in stressed zones with missing regulation data (ADR 0007).
- [ ] Deferred (ADR 0016): the scans and `purgar_solicitudes` are run by hand for now. Revisit before the first
      real deployment.
- [ ] Deferred (ADR 0007, last section): the legal scope of `comprobar_regulacion_alquiler` (habitual vs temporary
      leases, contract dates) is unverified and needs a lawyer. The scan stays as it is and is not extended; its
      alerts are a work aid, not proof of compliance.
- [x] Stay limits and `acepta_animales` moved to `TerminosAlquiler`, one per rental offer (ADR 0011). (3)
- [x] `CertificadoEnergetico` (one per listing): rating, consumption, emissions, number and dates; `eficiencia` and
      `nombre_eficiencia` were the same fact and became one letter A-G (ADR 0013). (1.8)
- [x] Community fees and IBI: amount and included flag now sit together on `Inmueble` (ADR 0011). The free-text
      `Condiciones.incluido` stays as the description. (1.9)

## 2. Remove derivable data

- [x] `InmuebleModalidad.mas_iva` dropped; `tipo_iva` is the source and `mas_iva` a property (ADR 0012). (1.5)
- [x] Same for `PlazaAparcamiento.precio_opcional_mas_iva` (ADR 0012). (1.5)
- [ ] Tie the optional parking price (and `precio_opcional_unidad`) to the price model; decide together with the
      `valor` / `renta` question in section 5. (1.6)
- [x] Location columns stay as three keys; consistency is checked in the models and by `comprobar_ubicaciones`
      (ADR 0006). (1.1)
- [x] `Comarca.provincia` dropped: a comarca can span provinces (ADR 0006). (1.1)
- [ ] Deferred (ADR 0006, addendum): a unified sub-municipal table (`Zona`). Revisit when a second city's districts /
      barrios are loaded and their real structure is known. (1.1)
- [x] `direccion_short` is a display override written by staff, documented on the field (ADR 0012). (1.10)
- [x] `Condiciones.modalidad` must equal the offer's modalidad: guarded by the model and scanned by
      `comprobar_condiciones` (ADR 0012). (1.7)

## 3. Repeating groups

- [x] `Transporte` to one row per mode: `TransporteInmueble(inmueble, tipo, descripcion)` (ADR 0008). (2.1)
- [x] `Suministro(inmueble, tipo, contador, compania, tipo_suministro)` for water, electricity and gas; heating
      type/subtype and gas type as choices (ADR 0008). (2.2)
- [x] `descripcion_es/en/cat` to `DescripcionInmueble(inmueble, idioma, texto)`; the API keeps flattening (ADR 0008). (2.3)
- [x] Free text with a closed domain to choices (ADR 0009): floor materials, carpentry, `tipo_fachada`,
      `tipo_cocina`, `situacion_actual`; `orientacion` is four flags and `Otros.office` was dropped (ADR 0009); `usos` stays
      free text. (2.5)
- [ ] Review the value lists with the agency's real vocabulary. For now ADR 0009 was widened with common market values
      (migration `0042`); the agency's own terms are still to be confirmed.
- [x] One convention for count vs boolean in `Dotacion`, `OtrosEspacios` (ADR 0010); `Instalaciones` and `Estancias`
      already follow it. (2.4)

## 4. Detail tables

- [x] `Banios` merged into `Dormitorios`, which became `Distribucion` (bedrooms, bathrooms, capacity) (ADR 0011). (3)
- [x] `Otros` split by concern (ADR 0011): `anio_ultima_reforma` and the included-in-the-rent flags to `Inmueble`,
      `capacidad_personas` to `Distribucion`, stay limits and pets to `TerminosAlquiler` (per rental offer), and
      the rest renamed `Caracteristicas`. (3)
- [x] A missing row is unknown and 0 is confirmed none; in `Distribucion` an empty count is unknown (ADR 0011). (3)
- [x] Checks: `exteriores <= dobles + individuales`, `sup_util <= sup_construida`, `fecha_baja >= fecha_alta`. (3)

## 5. Missing entities

- [x] Co-ownership: `InmueblePropietario(inmueble, propietario, porcentaje)` (ADR 0002).
- [x] `Propietario.nif` is unique when set (ADR 0013). (4)
- [x] The management agreement is `AcuerdoAdministracion`, with dates; `cat_nrc` became the private
      `Inmueble.referencia_catastral` instead of a `RegistroLegal` row, which is public (ADR 0013). (4)
- [x] `fecha_tasacion` dates the owner valuation; no history (ADR 0013). (4)
- [x] Audit columns on `InmuebleModalidad` and `Condiciones` (ADR 0013). (4)
- [x] Parking `valor` / `renta` stay internal notes outside the price model (ADR 0013). (4)

## 6. Naming consistency

- [x] The `_id` primary key of `Inmueble`, `ImageInmueble` and the location models is now `id` (ADR 0014). (5)
- [x] `Inmueble.TIPOS` codes are lowercase: `vivienda`, `oficina`, `local`, `parking`, `otro` (ADR 0014). (5)
- [x] Counts are `n_terrazas` / `n_balcones`; areas keep `_m2`; flags stay bare (ADR 0014). (5)

## 7. Cross-cutting (after each group lands)

- [ ] Update `MODELS.md` and the ER diagram.
- [ ] Update `seed/` and its tests for any changed reference data.
- [ ] Re-pin the public API with the allow-list tests; the fixtures in `backend/base/tests_ejemplos.py` must
      still load.
- [ ] Write an ADR for each decision that revises ADR 0001.

## 8. Gaps found in the examples (ADR 0019)

Source: second pass over `../gestion-inmobiliaria-examples`, now including locb-01..03. Decided out of scope: nightly
price unit / vacation modalidad, rooms, renaming modalidades (`habitual` is the long-term one), urbanización,
building/unit links, price tiers, availability wording, price-drop alerts.

### Step 1: agency and NRUA
- [x] `Agencia` (`nombre`, `aicat`, `numero_api`, contact); `Inmueble.agencia` optional, `PROTECT`; the detail returns
      `agencia`. `aicat` leaves `RegistroLegal` (migration `0043` moves existing rows).
- [x] `RegistroLegal`: type `nrua` and `estado` (`vigente`, `en_tramite`, `no_aplica`); only `vigente` may have a number.
- [x] Fixtures atb-01, atb-03 and idealista-03 updated; `MODELS.md` updated.
- [ ] Add fixtures for locb-01..03 to `tests_ejemplos.py` (agency 11525 / A13529, NRU in process, certificate with a
      rating but no number, half-bath, patio, smoking).
- [ ] Rename the agencies created by migration `0043` (`AICAT <number>`) in a real database; fill their API number.
- [ ] Frontend `interfaces.ts` still lists `aicat` as a registry type; update it when the backend is done.

### Step 2: unknown is not "no"; hidden address
- [x] `gran_tenedor`: `null` when the listing has no owner rows.
- [x] `zona_tensionada`: `null` when the municipality's declarations are not loaded; `Municipio.declaraciones_cargadas`
      says they are, and the seed command sets it for Catalonia. `comprobar_regulacion_alquiler` reports the unknown ones.
- [x] With `ocultar_direccion`, the detail returns coordinates snapped to a 0.005° grid (`OcultarDireccionMixin`).
- [ ] Mark `declaraciones_cargadas` in the admin for municipios outside Catalonia once their rules are known.
- [ ] Review whether the grid step (0.005°, about 550 m) is right for small towns, where one cell can hold few streets.

### Step 3: money (ADR 0020)
- [x] `InmuebleModalidad.fianza_meses` (1-12, rentals only); the API derives `fianza_total`. `Condiciones.fianza` stays text.
- [x] Sale costs: `Condiciones.itp_porcentaje` and `honorarios_incluidos_en_precio` (sale conditions only).
- [ ] VAT / AJD for new-build sales: waits for the agency to confirm the rule (no example page shows it).
- [x] `InclusionesAlquiler` per rental offer (community, IBI, insurance, wifi, utilities); `Inmueble.gastos_comunidad_incluidos`
      and `ibi_incluido` dropped (migration `0045` copies them to the rental offers).
- [x] `RegulacionAlquiler.indice_referencia_min` may be empty while the maximum is set (was already allowed; test added).
- [x] Fixtures `Locb01Test` to `Locb03Test` use the deposit months and the single index value (and every field above).
- [ ] Deposit limits by law (cap on months, regional deposit registry): needs a lawyer.

### Step 4: small additive fields (ADR 0021, migration `0046`)
Each candidate was checked against the existing models first.
- [x] `Distribucion.aseos` (half-baths).
- [x] `OtrosEspacios.patio` and `porche`; `Instalaciones.internet_velocidad_mbps` (only with internet).
- [x] `Dotacion`: `cafetera`, `plancha`, `kit_limpieza`, `secador_pelo`, `papel_higienico`, `sofa_cama`.
- [x] `TerminosAlquiler.acepta_fumadores` and `uso_temporada` (temporal offers only).
- [x] `ImageInmueble.TIPOS`: `piscina`, `detalles`.
- [x] `DescripcionInmueble.IDIOMAS`: `fr` and `it`.
- [x] Left out, no evidence in the examples: `CertificadoEnergetico.estado`, photo tag `entrada`, a `conservacion` level above
      "buen estado", internet type. Revisit if a real listing needs one.

### Step 5: scans (legal scope unverified, as in ADR 0007: work aids, not proof of compliance)
- [ ] Published temporal offer without an NRUA in force or in process.
- [ ] Stay limits by modalidad: temporal 32 days to 11 months; habitual above 11 months (locb-01 allows 6 months as the
      minimum of a long-term offer, so make this a warning). Warn when the description and the structured stay disagree
      (ATB-01, ATB-03).
- [ ] Habitual offer in a stressed zone with `precio` above `indice_referencia_max`.
- [ ] Sale offer without the cost fields filled (Ley 10/2025 clause in idealista-03).
- [ ] Soft warning on surface per bedroom (locb "8 bedrooms, 8 m2").
