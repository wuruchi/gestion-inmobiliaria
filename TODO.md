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
- [x] Moot (ADR 0022): the migrations were regenerated and no longer create placeholder declarations. Was: review the placeholders that migration `0020` created in an existing database (start date = the
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
      (the old migration `0042`, now folded into `0001_initial_uuid`); the agency's own terms are still to be confirmed.
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
      `agencia`. `aicat` leaves `RegistroLegal` (the old migration `0043` moved existing rows; migrations were regenerated in ADR 0022).
- [x] `RegistroLegal`: type `nrua` and `estado` (`vigente`, `en_tramite`, `no_aplica`); only `vigente` may have a number.
- [x] Fixtures atb-01, atb-03 and idealista-03 updated; `MODELS.md` updated.
- [x] Add fixtures for locb-01..03 to `tests_ejemplos.py` (agency 11525 / A13529, NRU in process, certificate with a
      rating but no number, half-bath, patio, smoking).
- [x] `python seed.py agencia` loads AtBarcelona (ATB, AICAT 5205).
- [ ] Fill the agency's API number in the admin when it is known.
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
      and `ibi_incluido` dropped (the old migration `0045` copied them to the rental offers).
- [x] `RegulacionAlquiler.indice_referencia_min` may be empty while the maximum is set (was already allowed; test added).
- [x] Fixtures `Locb01Test` to `Locb03Test` use the deposit months and the single index value (and every field above).
- [ ] Deposit limits by law (cap on months, regional deposit registry): needs a lawyer.

### Step 4: small additive fields (ADR 0021, formerly migration `0046`)
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

## 9. UUID primary keys (ADR 0022)
- [x] `Inmueble`, `InmuebleModalidad` and `SolicitudReserva` use UUIDv7 keys; the rest keep integers; migrations regenerated.
- [x] The detail-table serializers and `Condiciones` no longer return `id` / `inmueble`.
- [ ] Recreate the development database (and the Postgres schema, if used) before the next run.
- [ ] Run the backend suite against Postgres once a server is available (the change was only tested on SQLite).
- [ ] Frontend: listing ids become strings; the detail and reservation routes take a UUID.

## 10. Public API: offer-centred redesign (ADR 0023)
`InmuebleModalidad` (the offer) becomes the central public resource; `Inmueble` is nested inside it. Clean break under
`/api/v0`: the version is 0 on purpose, so the contract may still change without notice (the frontend is untouched until
the backend is done). Moving to `/api/v1` is the moment the contract is frozen.

### Decisions to settle first
- [x] Closed offers (rented, sold) in search: hidden by default behind `estado=`, their detail stays reachable.
- [x] Names: `ofertas` and `solicitudes` in Spanish.
- [x] Envelope: DRF `PageNumberPagination` (`count`, `next`, `previous`, `results`) plus `Link` header.

### Step 1: foundation and core resource
- [x] `REST_FRAMEWORK` settings: JSON-only renderer in production, default throttle, pagination, exception handler.
- [x] `/api/v0` prefix; remove `getRoutes` ('Hello') and the old `/inmuebles/modalidad/...` and `.../count/` routes.
- [x] Errors as `application/problem+json` (RFC 9457) with a field-level `errors` extension.
- [x] Pagination: `page_size` chosen by the client (capped at 50), out-of-range page is 404, `Link: rel=next/prev` (RFC 8288).
- [x] `GET /ofertas`: one row per offer; no `distinct()`, no per-inmueble state annotations.
- [x] Filters: `modalidad`, `municipio`, `distrito`, `barrio` (id or slug), `precio_min`, `precio_max`, `habitaciones_min`,
      `banios_min`, `sup_min`, `sup_max`, `tipo`, `subtipo`, `disponible_antes`.
- [x] Feature filters: `amueblado`, `animales`, `piscina`, `parking`, `ascensor`, `terraza`.
- [x] `sort`: `precio`, `-precio`, `-fecha_alta`, `sup`.
- [x] Card payload (price object, `fianza`, state, availability, main image, headline numbers) and detail payload
      (`regulacion`, `terminos`, `inclusiones`, `condiciones` at the top level of the offer, `inmueble` nested,
      `otras_ofertas`, `agencia`).
- [x] Money as decimal string plus `moneda`; `precio.por_m2` derived; dates RFC 3339.
- [x] `GET /ofertas/{id}`: `ETag` and conditional GET; unpublished offer is 404.
- [x] `POST /ofertas/{id}/solicitudes`: 201 with `Location`, keeps the 10/hour throttle, 429 with `Retry-After`.
- [x] Tests pinning the public fields of the offer card and detail (private data never serialized, as today).
- [ ] Decide whether a request should record the offer it was about (`SolicitudReserva.oferta`, ADR 0023); today it keeps only the listing.
- [ ] Set `NUM_PROXIES` (or the real client-IP header) before deploying behind a proxy: the throttles are per IP.
- [x] The API tests also pass with `DJANGO_DEBUG` unset (JSON-only renderer): `DJANGO_SECRET_KEY=x DJANGO_ALLOWED_HOSTS=testserver python manage.py test base.tests.ApiOfertasTests`.
- [x] `MODELS.md` and an ADR describing the API.

### Step 2: reference data
- [x] `GET /municipios?provincia=&q=`, `/distritos?municipio=`, `/barrios?distrito=` replace the nested paths; paginated (parent by id or slug).
- [x] `GET /catalogos`: types, subtypes, conservation and modalidades (replaces `/modalidades`).
- [x] `GET /agencia`: public agency data (name, AICAT, API number); the first agency created, 404 without one.
- [x] `Cache-Control: public, max-age=3600` on reference data.

### Step 3: discovery
- [ ] Deferred (favourites are out of scope for now): `GET /ofertas?id=a,b,c`, batch fetch for client-side favourites.
- [ ] Deferred (out of scope for now): `GET /ofertas/{id}/similares`, same zone and modalidad, similar price.
- [x] `GET /ofertas/mapa`: same filters, GeoJSON (RFC 7946), minimal properties, `bbox=`; hidden addresses stay snapped (the `bbox` is checked against the snapped point). At most 1000 features, then `truncated: true`.
- [ ] Deferred (later in development): `GET /ofertas/facetas`, counts per district, type and room number for the current filters (each count must ignore its own filter).
- [x] `Accept-Language` picks `inmueble.descripcion` (`{idioma, texto}`) in the detail; `descripciones` keeps every language; `Vary: Accept-Language`.

### Step 4: later
- [ ] `GET /estadisticas/precios?municipio=`: price per m² per zone (idealista "Informe de precios", locb).
- [ ] Deferred by decision: OpenAPI schema with `drf-spectacular`. Plan when it is taken up: `@extend_schema` on the
      offer views (filters built from the table in `filtros_ofertas.py`, pagination envelope, problem+json errors,
      `Link`/`ETag`/`Retry-After`, `application/geo+json`), type hints on the `SerializerMethodField`s, a committed
      `openapi.yaml` with a test that fails when it differs from the generated one, the schema and Swagger/Redoc UI
      under `/api/v0/`, and a short `docs/api.md` for conventions, privacy rules and the versioning policy.
- [ ] Freeze the contract and publish it as `/api/v1`; from then on retire versions with the `Sunset` header (RFC 8594).
- [ ] Frontend: move to `/ofertas` after the backend is declared done.

## 11. Public web: Next.js, SEO first (ADR to write: `0024`)

Goal: every offer is easy to advertise: a shared link shows a title, description and image that carry the offer's key
details and the company, and search engines index the offers and the zone pages. The old CRA app in `frontend/` stays
as a reference until the new app in `web/` reaches parity; then both it and `publish.sh` are removed in one commit.

### Decisions to settle first
- [x] Framework: Next.js (App Router, Server Components by default, `"use client"` only for the gallery, map and form).
- [x] New app in `web/` next to `frontend/`.
- [ ] Hosting: Node runtime (Vercel, or a container beside Django); how the web app reaches the API (`API_URL`).
- [ ] Canonical offer URL: `/ofertas/{slug}-{uuid}` (proposed); the UUID suffix decides, a wrong slug redirects (308).
- [ ] Languages: Spanish only at first, or `hreflang` from the start (the API already honours `Accept-Language`).
- [ ] Closed offers (rented, sold): keep indexable for a period, or `noindex` + out of the sitemap, then redirect to the zone page.
- [ ] Revalidation: time-based (proposed 5 min) plus an on-demand webhook from Django on offer changes. Next 16 has
      Cache Components on: caching is opt-in with `'use cache'` + `cacheLife` + `cacheTag` (not `fetch(..., {next: {revalidate}})`),
      uncached reads must sit inside `<Suspense>`. Read `web/node_modules/next/dist/docs/01-app/` before writing pages (see `web/AGENTS.md`).

### Step 0: environment
- [x] Install Node LTS and npm on the dev machine (nvm, Node 24; non-login shells do not see it: use `zsh -lic`).
- [x] `web/` scaffold: TypeScript, App Router, ESLint, Sass, `.env.example` (`API_URL`, `SITE_URL`), `.nvmrc`; lint and build pass.
- [ ] Port the styles from `frontend/sass/` as the pages need them (not wholesale).
- [x] Next.js 16.4.3, React 19.3.0 and Sass pinned to exact versions (`engines.node >=24`).
- [ ] Note the Cache Components model of the pinned version in the ADR.

### Step 1: backend gaps the web needs (additive, ADR 0024)
- [ ] Offer slug in the API (derived and stable enough that old links keep working through the UUID suffix).
- [ ] `updated_at` on the offer (for `lastmod`) and a cheap way to list every public offer id for the sitemap.
- [ ] Agency: logo and public contact data in `/agencia` and in the offer detail (share card, `RealEstateAgent` schema).
- [ ] Photos: URL, width, height and alt text, main photo flagged; absolute URLs; a size suitable for a 1200x630 card.
- [ ] Webhook (signed) from Django to the web app on publish, change and unpublish of an offer (`revalidateTag`).
- [ ] `Cache-Control`/`ETag` on the offer detail and list so the web server can revalidate cheaply; CORS origin for the web host.
- [ ] Tests for each new field; update `MODELS.md`.

### Step 2: foundation
- [ ] `lib/api.ts`: typed wrappers for `/ofertas`, `/ofertas/{id}`, `/ofertas/mapa`, `/catalogos`, `/agencia`, places; problem+json errors; revalidation tags.
- [ ] Types for the API payloads, kept in one place (generated from the OpenAPI schema if it exists by then).
- [ ] Root layout: `lang`, site-wide metadata (`metadataBase`, title template, default Open Graph/Twitter), header, footer with legal notice (AICAT, API number, NRUA).
- [ ] `Organization`/`RealEstateAgent` JSON-LD site-wide; favicon, manifest, theme colour.
- [ ] Error, not-found and loading pages; consistent `notFound()` for unpublished offers.

### Step 3: offer page (vertical slice, build first)
- [ ] `/ofertas/[slug]`: server-rendered detail, redirect to the canonical slug, closed-offer notice.
- [ ] `generateMetadata`: title, description (price, rooms, surface, zone), canonical, Open Graph, Twitter card, `alternates`.
- [ ] JSON-LD: `RealEstateListing` + `Offer` (price, currency, availability) + residence type + `BreadcrumbList`.
- [ ] `opengraph-image.tsx`: branded 1200x630 card (photo, price, modality, zone, logo); fallback when there is no photo; cached.
- [ ] Gallery (client component, responsive images with dimensions, first image preloaded).
- [ ] Request form (client component) posting to `/ofertas/{id}/solicitudes/`: validation from the 400 `errors`, 429 `Retry-After` message, consent checkbox.
- [ ] Rental regulation, terms, inclusions and conditions sections; hidden-address offers show the approximate area only.
- [ ] Other offers of the same listing (`otras_ofertas`) linked.

### Step 4: crawlability
- [ ] `sitemap.ts` (offers with `lastmod`, zone pages; split into several sitemaps past 50 000 URLs) and `robots.ts` pointing to it.
- [ ] Canonical, pagination (`rel` links) and `noindex` rules for filtered or empty result pages.
- [ ] Zone landing pages `/{modalidad}/{municipio}[/{distrito}[/{barrio}]]` (and by type), with their own metadata, intro text and `ItemList` JSON-LD.
- [ ] Redirects for old CRA routes if any were public.
- [ ] `hreflang` if more than one language is published.

### Step 5: search and map
- [ ] `/buscar`: filters live in the URL (`searchParams`), real `<a href>` pagination, no infinite scroll.
- [ ] Offer card (server component) with the same price/state rules as the detail.
- [ ] Filter form (client component) built on `/catalogos` and the place endpoints; every bad value reported from the 400.
- [ ] Map view on `/ofertas/mapa` (GeoJSON, `bbox`, `truncated` notice); client component loaded lazily; replace the Google Maps loader if a lighter option fits.
- [ ] Home page: featured zones and offers.

### Step 6: quality
- [ ] Rendered HTML check: `curl` each page type and assert title, description, canonical, Open Graph and JSON-LD are present without JavaScript.
- [ ] Tests (unit for `lib/`, component tests for the form, a few end-to-end checks of the offer page).
- [ ] Share previews checked by hand: Facebook Sharing Debugger, LinkedIn Post Inspector, WhatsApp, X; Google Rich Results Test.
- [ ] Lighthouse budget (performance, SEO, accessibility) per page type; image formats (AVIF/WebP), fonts, third-party scripts.
- [ ] Accessibility pass (labels, focus, contrast, keyboard in gallery and map).
- [ ] Privacy: no cookies or trackers before consent; analytics decision.

### Step 7: deploy and retire the old app
- [ ] Deployment recipe (build, env, health check), CDN caching, and the Django side (`ALLOWED_HOSTS`, CORS, `NUM_PROXIES`).
- [ ] Google Search Console and Bing Webmaster: verify the domain, submit the sitemap.
- [ ] Remove `frontend/` and `publish.sh`; update `README.md` and the ADR.
- [ ] Frontend items of section 10 (`/ofertas`, favourites, similar offers, facets) picked up here when they are taken up.
