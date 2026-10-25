# ADR 0022: UUIDv7 primary keys for listings, offers and requests

- Status: Accepted (migrations regenerated: `0001_initial_uuid`)
- Revises: ADR 0014 (the `id` primary key of `Inmueble` is no longer an auto-increment integer).

## Context

The listing id is in the public URL (`/api/inmuebles/<id>/`), so sequential integers let anyone enumerate listings
and read their number. Listings will also be created by an importer and may be merged between databases, and
requests hold personal data. The database is a development one, so the cost of changing keys is lowest now.

## Decisions

- **`Inmueble`, `InmuebleModalidad` and `SolicitudReserva` have a `UUIDField(primary_key=True)`** filled with a
  UUIDv7 (time-ordered, so Postgres index inserts stay almost sequential; `uuid.uuid7` on Python 3.14, otherwise
  the `uuid-utils` package: `base/models/ids.py`). The key exists before the first save, so code must not use
  `pk is None` to detect a new row: the audit mixin and the price log use `_state.adding`.
- **Everything else keeps an integer key**: the locations, `Modalidad` and the other reference data (their ids
  must be the same in every environment), the one-to-one detail tables (never addressed alone), and the child rows
  (images, media, parking, registrations, supplies, transport, descriptions, price log, agreements, owner links).
  Several of them order by `['posicion', 'id']`; with v7 the id still follows creation order.
- **API**: `id` of a listing is a UUID string; the routes use `<uuid:pk>`, so any other value is a 404. The detail
  tables, the four `Estancias` blocks and `Condiciones` no longer return `id` or `inmueble` (the serializers now
  `exclude` them instead of using `'__all__'`). Images and parking spaces keep their integer `id`.
- **Migrations were regenerated**: a primary key cannot change type in place across about 25 foreign keys. The 47
  old migrations are gone and the single `0001_initial_uuid` replaces them. It is not called `0001_initial` on
  purpose: against an old database it fails loudly ("table already exists") instead of being skipped as
  already applied. **Recreate the development database** (delete the SQLite file, or drop and recreate the
  Postgres schema), then `python seed.py migrate` and the seed commands.

## Consequences

- The data migrations of the old history disappeared with it (the AICAT-to-agency copy, the included-in-rent flags,
  the municipality flag); a new database does not need them.
- `Agencia` seed no longer renames migration placeholders, because none are created any more.
- The frontend types (`id: number` of a listing) must become strings when the backend is declared done.
- Not tested on Postgres in this change (no local server): Django maps `UUIDField` to the native `uuid` type there.
  Run the suite against Postgres before the first deployment.
- Staff-visible references stay `referencia` (`DEV-0001`, `G767`); the UUID is for machines.
