# ADR 0023: Offer-centred public API under `/api/v0`

- Status: Accepted (step 1 of TODO section 10: foundation and the core resource; reference data and discovery follow)
- Revises: ADR 0001 (the `/reservas/` endpoint is now `/ofertas/{id}/solicitudes/`), ADR 0004 and ADR 0017 for the API only (the listing-level `estado` and `fecha_disponibilidad` are no longer
  returned; the model properties stay), ADR 0022 (the public URL is the offer's UUID, not the listing's).

## Context

The public API was listing-centred: one row per `Inmueble`, with its offers (`modalidades`) inside. That forced
`distinct()` on every search, per-listing state annotations (`orden_estado`, `proxima_disponibilidad`), a rule for
"which offer does `max_precio` mean" and several derived fields (`es_venta`, `importe_alquiler`, `importe_venta`,
listing `estado`). A visitor does not choose a flat: they choose to rent it or to buy it, and each of those has its own
price, deposit, state, date, conditions and regulation. The offer (`InmuebleModalidad`) is the thing that is searched,
shown and asked about.

## Decisions

- **The offer is the public resource**; the listing is nested in it. The contract is versioned by the path:
  `/api/v0` is a version zero on purpose, so it may change without notice until the backend is declared done.
  Moving to `/api/v1` freezes it.
- **Names in Spanish**: `ofertas`, `solicitudes`. Routes: `GET /ofertas/`, `GET /ofertas/{id}/`,
  `POST /ofertas/{id}/solicitudes/`. The id is the offer's UUIDv7. The old `/api/inmuebles/...`, the count route and the
  `Hello` route were removed (no redirect: nothing else uses them).
- **One row per offer in the search.** No `distinct()`, no per-listing state annotations. A listing offered for rent and
  for sale appears twice, once per offer.
- **Closed offers (rented, sold) are hidden by default.** `estado=` takes one or more of `disponible`, `reservado`,
  `cerrado` (comma separated); the default is `disponible,reservado`. The detail of a closed offer stays reachable, so a
  shared link does not break. Only an unpublished listing is a 404.
- **Envelope**: DRF `PageNumberPagination`: `count`, `next`, `previous`, `results`, plus the same links in a `Link`
  header (RFC 8288, `rel="next"` / `rel="prev"`). `page_size` is chosen by the client, default 20, capped at 50. A page
  out of range is a 404.
- **Errors are `application/problem+json`** (RFC 9457): `type` (`about:blank`), `title` (the HTTP reason), `status`,
  `detail` and, for a 400, `errors` as `{field: [messages]}`. Every bad query parameter is reported at once. `Retry-After`
  of a 429 is kept. The 404 message is generic (Django's names the model).
- **Filters** (all optional, any bad value is a 400 naming the field): `modalidad`, `estado`, `municipio`, `distrito`,
  `barrio` (id or slug; a slug is unique only inside its parent, so it may match several places), `tipo`, `subtipo`,
  `precio_min`, `precio_max` (the offer's own price as advertised, net of VAT), `sup_min`, `sup_max` (built surface),
  `habitaciones_min` (same sum as `Inmueble.n_habitaciones`; unknown never matches), `banios_min`, `disponible_antes`
  (the offer's own `fecha_disponibilidad`), and the feature flags `amueblado`, `animales` (the rental's terms),
  `piscina`, `ascensor`, `terraza` (at least one terrace), `parking` (a parking space or a parking listing).
  A feature flag accepts only `true`/`1`: a missing detail row is unknown, not "no", so there is no "without" filter.
  `sort` is `precio`, `-precio`, `-fecha_alta` or `sup` (unknown surface last); the default is available, then
  reserved, then closed, by the soonest `fecha_disponibilidad`. Ties break on the id, which is time ordered.
  The old `provincia`, `referencia`, `habitaciones` (exact), `max_precio` and `fecha_entrada` are gone.
- **Payloads.** The card: `id`, `modalidad`, `precio`, `fianza`, `estado`, `fecha_disponibilidad` and a light
  `inmueble` (identity, place, headline numbers, main photo). The detail adds `regulacion`, `terminos`, `inclusiones`
  and `condiciones` at the top level of the offer, the full `inmueble`, `otras_ofertas` (the listing's other offers, as
  summaries) and `agencia` (it left the listing).
- **Money** is a decimal string with `moneda` (`EUR`). `precio` is an object: `importe`, `moneda`, `unidad`, `mas_iva`,
  `tipo_iva`, `por_m2` (price over built surface, null without it). `fianza` is `{meses, importe, moneda}` or null.
  Dates are RFC 3339.
- **Requests**: `POST /ofertas/{id}/solicitudes/` answers 201 with a `Location` and the new `id`. It keeps the limit of
  10 per hour per client (429 with `Retry-After`). The request is still stored against the listing, not the offer.
  `Location` identifies the request but the public cannot read it back: it holds personal data.
- **Defaults** (`REST_FRAMEWORK`): JSON-only renderer (the browsable API only with `DEBUG`), an anonymous throttle of
  120 per minute (`DJANGO_THROTTLE_ANON`), the problem handler, and `ConditionalGetMiddleware`: every GET carries an
  `ETag` and answers 304 to a matching `If-None-Match`. The ETag is a hash of the body, so it saves bandwidth, not
  work. CORS exposes `Link`, `ETag`, `Location` and `Retry-After`.

## Consequences

- Removed from the listing payload: `modalidades`, `es_venta`, `importe_alquiler`, `importe_venta`, `estado`,
  `fecha_disponibilidad`, `agencia`, and from the card the descriptions and the full detail tables (they are in the
  detail). `Inmueble.estado` and `Inmueble.fecha_disponibilidad` remain as model properties.
- The frontend cannot talk to this API until it is moved to `/ofertas` (out of scope until the backend is done).
- A request does not record which offer it was about. If staff need that (a flat offered both ways), add an optional
  `oferta` link to `SolicitudReserva`; not done here.
- The throttle is per IP; behind a proxy, `NUM_PROXIES` must be set or every visitor shares one bucket.
- Test suite: the test settings raise the anonymous limit, because all tests share one address and one cache; the
  throttle tests set their own rate.
- **Reference data (step 2).** `GET /provincias/`, `/municipios/?provincia=&q=`, `/distritos/?municipio=`,
  `/barrios/?distrito=` (a parent is an id or a slug; paginated with the same envelope, 100 per page, up to 500),
  `/catalogos/` (`tipos`, `subtipos`, `conservaciones`, `estados`, `modalidades`) and `/agencia/` (`nombre`, `aicat`,
  `numero_api`) all send `Cache-Control: public, max-age=3600`. The nested paths and `/modalidades/` were removed.
  `/agencia/` returns the first agency created (the seed loads the main one first) and 404 without one; with several
  agencies a flag for "the site's agency" would be needed.
- **Map (step 3).** `GET /ofertas/mapa/` takes the search filters plus `bbox=minLon,minLat,maxLon,maxLat` and returns a
  GeoJSON `FeatureCollection` (`application/geo+json`) with one `Point` (lon, lat) per offer and minimal properties
  (`modalidad`, `tipo`, `estado`, `precio`, `moneda`, `unidad`); the feature `id` is the offer's. Listings without a point
  are left out. A hidden address is placed at its snapped point, and the `bbox` is tested against that snapped point
  (the database only pre-filters with a margin of one grid step): testing the real one would let a client shrink a box
  until it found the exact position. At most 1000 features; beyond that `truncated` is `true`.
- **Language (step 3).** The detail has `inmueble.descripcion` = `{idioma, texto}` chosen from `Accept-Language`
  (q-values respected, region ignored; no match falls back to Spanish, then to the first language available; `null`
  without descriptions). `descripciones` still returns every language, and the response has `Vary: Accept-Language`.
- Deferred by decision: batch fetch of favourites (`?id=a,b,c`), `similares` and `facetas`. Still to do: statistics,
  OpenAPI and the freeze.
