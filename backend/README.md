# atbarcelona-new
New AtBarcelona design

## Configuration (environment variables)
- `DJANGO_SECRET_KEY` (required unless `DJANGO_DEBUG=1`)
- `DJANGO_DEBUG=1` for local development
- `DJANGO_ALLOWED_HOSTS`, `DJANGO_CORS_ORIGINS` (comma separated)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` for Postgres (SQLite if `DB_NAME` unset)
- `DJANGO_MEDIA_ROOT` where uploaded photos are stored (default `./media`, served at `/media/`)

## Local development
```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # Python 3.13
export DJANGO_DEBUG=1
python manage.py migrate && python manage.py createsuperuser
python manage.py runserver        # API on http://localhost:8000/api, admin on /admin/
```

## Seeding
Location data (province, comarcas, municipios, distritos, barrios) is loaded by the separate
`../seed` tool; see its README.
