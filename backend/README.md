# backend

Django REST API and admin for the AtBarcelona real-estate listings. It also serves the built
frontend (`staticfiles/`) in development.

Python 3.13, Django 5.2 LTS, Django REST Framework. SQLite by default, Postgres when `DB_NAME` is set.

## Local development
```
cd backend
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DJANGO_DEBUG=1
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver        # API on http://localhost:8000/api/v0/, admin on /admin/
```
A new database is empty. Load the locations and modalidades with the [seed](../seed/README.md) tool
(it can also run `migrate` for you), then add listings in the admin.

## Configuration (environment variables)
| Variable | Meaning |
|---|---|
| `DJANGO_DEBUG` | `1` for local development. Without it `DJANGO_SECRET_KEY` is required. |
| `DJANGO_SECRET_KEY` | Secret key (required unless `DJANGO_DEBUG=1`). |
| `DJANGO_ALLOWED_HOSTS`, `DJANGO_CORS_ORIGINS` | Comma-separated lists. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Postgres. SQLite is used when `DB_NAME` is unset. |
| `DB_SQLITE_PATH` | SQLite file (default `backend/db.sqlite3`). |
| `DJANGO_MEDIA_ROOT` | Where uploaded photos are stored (default `./media`, served at `/media/`). |

Django only serves `/media/` and `/img/` while `DEBUG` is on. Behind a real web server, serve them from it.
The database settings live in `backend/database.py`, shared with the seed tool.

## Data model (`base/models/`)
- **Locations:** `Provincia` > `Municipio` > `Distrito` > `Barrio`; a `Comarca` only groups municipios (it has no
  province: Cerdanya spans two). Official codes (`codigo_ine`), slugs and unique constraints; all links are `PROTECT`.
  The listing's municipio/distrito/barrio must nest; `python manage.py comprobar_ubicaciones` scans for violations
  (bulk writes skip the model checks) and fails if it finds any.
- **Offer conditions:** an offer's `Condiciones` must be of its own modalidad (model checks);
  `python manage.py comprobar_condiciones` scans for violations that skipped them. See ADR 0012.
- **`Inmueble`:** the listing. Links to the locations, to `Modalidad` through `InmuebleModalidad`
  (several allowed: temporal, habitual, venta) (each with its price, VAT and optional `Condiciones`). Carries the regulatory fields
  (last rent, reference index, tensioned zone, large holder) and the energy label.
  `municipio` is required and `provincia` is derived from it; `clean()` and `save()` reject a barrio or district that does not nest. The town and zone are not stored:
  the API's `zona` / `zona_ref` are the barrio and district names. Dates are dates (no time); prices, surfaces
  and counts cannot be negative (validators and database constraints). Distances in metres (`distancia_*_m`), the real height in metres (`altura_real_m`).
- **Detail tables** (one optional row per listing, linked by `inmueble`): `Distribucion` (bedrooms, bathrooms, capacity), `Estancias` (living
  room, terrace, kitchen, carpentry; the API still returns them as `salon`, `terraza`, `cocina`, `carpinteria`), `OtrosEspacios`, `Dotacion`, `Instalaciones`, `Seguridad`, `Entorno`,
  `AreaRecreo`, `Caracteristicas`. They are the single source for equipment. A missing row means unknown, and in
  `Distribucion` an empty count is unknown while 0 is confirmed none (ADR 0011). Stay limits and pets are
  `TerminosAlquiler`, one per rental offer; `anio_ultima_reforma` and the included-in-the-rent flags are on `Inmueble`.
- **Closed lists.** Columns with a closed vocabulary are choices, not free text: floor materials (`suelo_piso`,
  `Distribucion.suelo_banio`, `suelo_cocina`, in `models/opciones.py`), carpentry material, `tipo_fachada`, `tipo_cocina`,
  `situacion_actual` (the lists were drafted from the examples and widened, ADR 0009). The API returns the lowercase value (`parquet`, `alquiler_vacacional`). `usos` stays free
  text. Orientation is four flags (`orientacion_norte/sur/este/oeste`) because a listing can face several ways.
- **Count or flag.** In the equipment tables an item is a count only when having two is plausible and the number
  matters (`camas`, `sofas`, `trastero`...); otherwise it is a yes/no flag (`lavadora`, `bodega`...). See ADR 0010.
- **Repeating groups** have one row per member instead of one column set per member: `Suministro` (water,
  electricity, gas), `TransporteInmueble` (one per mode) and `DescripcionInmueble` (one per language). The API
  flattens supplies and transport to the keys it always had (`instalaciones.contador_agua`, `transporte.cerca_metro`;
  the descriptions are the object `descripciones: {es, en, ca}`, with only the languages that exist); `instalaciones` and `transporte` are `null` when there are no rows. The list and the
  detail prefetch `descripciones` and `suministros` (and `transportes` in the detail), so the query count does not
  grow with the page size.
- **Prices:** `InmuebleModalidad` holds one required, non-negative `precio` per listing and modalidad.
  `Modalidad.unidad_precio` says whether it is monthly or a total. A modalidad in use cannot be deleted.
  The API returns `modalidades: [{codigo, nombre, unidad_precio, precio}]` (the detail also has, per rental modalidad, `regulacion`: reference index and last rent, see `RegulacionAlquiler`, and `terminos`: stay limits and pets); `importe_alquiler` (lowest monthly
  price) and `importe_venta` are derived from it for the frontend.
- **Rooms:** `n_habitaciones` is computed (`Distribucion`: dobles + individuales; suites and exteriores are subsets), not stored, and `null` when unknown. `n_banios` is `Distribucion.banios`, `null` when unknown.
- **Parking:** `PlazaAparcamiento` (many per listing: number, type, surface, notes, optional price; value and rent are private).
  `n_plz_garaje` in the API is the count of plazas. A parking space on its own is a listing with `tipo='parking'`.
- **Photos:** `ImageInmueble` (`ImageField`, `tipo`, `posicion`, `alt_text`, one `default` photo per listing; floor plans are `tipo='plano'`). `MediaInmueble`: videos and virtual tours by link.
- **Private (never in the API):** `Propietario` (owners, with `gran_tenedor`), `InmueblePropietario` (listing ↔ owners, many to many), `DatosInternos` (one per listing: internal
  notes, owner valuation and its date), `AcuerdoAdministracion` (management agreements with dates), `HistorialPrecio` (price by date and modalidad; our own price log). `created_by` / `updated_by` (on `Inmueble`, `InmuebleModalidad` and `Condiciones`) are set by the admin. The energy certificate is `CertificadoEnergetico` (public, one per listing).
- **Other:** `SolicitudReserva` (reservation, visit or information requests: `tipo`, optional `mensaje`; `estado` pendiente / contactada / cerrada / descartada).
  Personal data is kept 12 months: schedule `python manage.py purgar_solicitudes` (options `--meses N`, `--dry-run`),
  which blanks name, email and phone on older requests and keeps the rest of the row.

## API (`/api/v0/`)
A version zero: the contract may change until the backend is declared done (ADR 0023). The offer is the resource.

| Endpoint | Description |
|---|---|
| `GET ofertas/` | One card per offer of a published listing, paginated (`page_size` up to 50, `Link` header). |
| `GET ofertas/<uuid>/` | Offer detail: price, deposit, conditions, regulation, terms, inclusions, the full listing and its other offers. |
| `GET ofertas/mapa/` | GeoJSON points for the same filters, plus `bbox=minLon,minLat,maxLon,maxLat` (max 1000). |
| `POST ofertas/<uuid>/solicitudes/` | Reservation, visit or information request (`tipo`, optional `mensaje`; limited to 10 per hour per client). |
| `GET provincias/`, `municipios/?provincia=&q=`, `distritos/?municipio=`, `barrios/?distrito=` | Reference lists (parent by id or slug; paginated except provinces). Cacheable for an hour. |
| `GET catalogos/`, `GET agencia/` | Closed lists (types, subtypes, conservation, states, modalidades) and the public agency data. |

Filters of `ofertas/`: `modalidad`, `estado` (default `disponible,reservado`), `municipio`, `distrito`, `barrio` (id or
slug), `tipo`, `subtipo`, `precio_min`, `precio_max`, `sup_min`, `sup_max`, `habitaciones_min`, `banios_min`,
`disponible_antes`, `amueblado`, `animales`, `piscina`, `parking`, `ascensor`, `terraza` (only `true`), `sort`
(`precio`, `-precio`, `-fecha_alta`, `sup`). Errors are `application/problem+json`; a bad parameter is a 400 with
`errors` per field. Every GET has an `ETag`. The anonymous throttle is `DJANGO_THROTTLE_ANON` (default `120/min`).

Only listings with `publicar_web` are returned. The listing serializer is an allow-list
(`INMUEBLE_PUBLIC_FIELDS` in `base/serializers.py`); a test fails if a new `Inmueble` column is not
classified as public or private, so owner and internal data cannot leak by default.

## Tests
```
DJANGO_DEBUG=1 DJANGO_ALLOWED_HOSTS=testserver python manage.py test
```

## Migrations
The history is a single migration, `0001_initial_uuid` (ADR 0022). It cannot be applied over a database created by the
old migrations: it fails with "table already exists". Recreate the development database (delete the SQLite file, or
drop and recreate the Postgres schema), then run `python seed.py migrate` and the seed commands.
