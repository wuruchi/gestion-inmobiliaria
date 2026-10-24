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
python manage.py runserver        # API on http://localhost:8000/api/, admin on /admin/
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
- **`Inmueble`:** the listing. Links to the locations, to `Modalidad` through `InmuebleModalidad`
  (several allowed: temporal, habitual, venta) (each with its price, VAT and optional `Condiciones`). Carries the regulatory fields
  (last rent, reference index, tensioned zone, large holder) and the energy label.
  `municipio` is required and `provincia` is derived from it; `clean()` and `save()` reject a barrio or district that does not nest. The town and zone are not stored:
  the API's `zona` / `zona_ref` are the barrio and district names. Dates are dates (no time); prices, surfaces
  and counts cannot be negative (validators and database constraints). Stay limits are in months
  (`estancia_*_meses`), distances in metres (`distancia_*_m`), the real height in metres (`altura_real_m`).
- **Detail tables** (one optional row per listing, linked by `inmueble`): `Dormitorios`, `Banios`, `Estancias` (living
  room, terrace, kitchen, carpentry; the API still returns them as `salon`, `terraza`, `cocina`, `carpinteria`), `OtrosEspacios`, `Dotacion`, `Instalaciones`, `Seguridad`, `Entorno`,
  `Transporte`, `AreaRecreo`, `Otros`. They are the single source for equipment and stay limits.
- **Prices:** `InmuebleModalidad` holds one required, non-negative `precio` per listing and modalidad.
  `Modalidad.unidad_precio` says whether it is monthly or a total. A modalidad in use cannot be deleted.
  The API returns `modalidades: [{codigo, nombre, unidad_precio, precio}]` (the detail also has `regulacion` per rental modalidad: reference index and last rent, see `RegulacionAlquiler`); `importe_alquiler` (lowest monthly
  price) and `importe_venta` are derived from it for the frontend.
- **Rooms:** `n_habitaciones` is computed (`Dormitorios`: dobles + individuales; suites are a subset), not stored.
- **Parking:** `PlazaAparcamiento` (many per listing: number, type, surface, notes, optional price; value and rent are private).
  `n_plz_garaje` in the API is the count of plazas. A parking space on its own is a listing with `tipo='Parking'`.
- **Photos:** `ImageInmueble` (`ImageField`, `tipo`, `posicion`, `alt_text`, one `default` photo per listing; floor plans are `tipo='plano'`). `MediaInmueble`: videos and virtual tours by link.
- **Private (never in the API):** `Propietario` (owners, with `gran_tenedor`), `InmueblePropietario` (listing ↔ owners, many to many), `DatosInternos` (one per listing: internal
  notes, `cat_nrc`, signing date), `HistorialPrecio` (price by date and modalidad; our own price log). `Inmueble.created_by` / `updated_by` are set by the admin.
- **Other:** `SolicitudReserva` (reservation, visit or information requests: `tipo`, optional `mensaje`; `estado` pendiente / contactada / cerrada / descartada).
  Personal data is kept 12 months: schedule `python manage.py purgar_solicitudes` (options `--meses N`, `--dry-run`),
  which blanks name, email and phone on older requests and keeps the rest of the row.

## API (`/api/`)
| Endpoint | Description |
|---|---|
| `GET inmuebles/` | Published listings, paginated (5 per page). |
| `GET inmuebles/modalidad/{temporales,habituales,ventas}/` | Same, filtered by modalidad. |
| `GET inmuebles/<id>/` | Listing detail, including the detail tables and rental conditions. |
| `POST inmuebles/<id>/reservas/` | Reservation, visit or information request (`tipo`, optional `mensaje`; limited to 10 per hour per client). |
| `GET inmuebles/modalidad/<modalidad>/distrito/<id>/count/` | Number of published listings. |
| `GET provincias/`, `municipios/`, `distritos/`, `modalidades/` | Reference lists. |
| `GET provincias/<id>/municipios`, `municipios/<id>/distritos`, `distritos/<id>/barrios` | Children of a location. |

List filters (query string): `page`, `provincia`, `municipio`, `distrito`, `barrio`, `referencia`,
`habitaciones`, `max_precio`, `fecha_entrada`. A non-numeric value returns 400.
`max_precio` compares the price of the modalidad in the URL (`ventas`: the sale price); on `inmuebles/`
it compares the monthly (rent) prices.

Only listings with `publicar_web` are returned. The detail serializer is an allow-list
(`INMUEBLE_PUBLIC_FIELDS` in `base/serializers.py`); a test fails if a new `Inmueble` column is not
classified as public or private, so owner and internal data cannot leak by default.

## Tests
```
DJANGO_DEBUG=1 DJANGO_ALLOWED_HOSTS=testserver python manage.py test
```

## Migrations
Migrations `0022` and `0028` refuse to run when the tables they restructure already contain rows
(locations and listings respectively). On a database with data, map the old values by hand first.
