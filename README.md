# gestion-inmobiliaria

Real-estate listings platform for AtBarcelona: a public site to search and view rental and sale
listings in the province of Barcelona, and an admin to manage them.

| Folder | What it is |
|---|---|
| [`backend/`](backend/README.md) | Django REST API and admin. Owns the data model and serves the built frontend. |
| [`frontend/`](frontend/README.md) | React site (search, results, listing detail, map). |
| [`seed/`](seed/README.md) | Standalone tool that loads reference data (locations, modalidades) into the backend's database. |

These are plain folders of one repository, not separate repositories.

## How the parts fit
```
official open data --> seed --> database <-- backend (API + admin) <-- frontend
                                    ^                |
                                    |                +-- serves frontend build (staticfiles/)
                          same DB_* settings (backend/database.py)
```
- `seed` imports the backend's models, so there is one schema. It needs the same database settings
  as the backend, otherwise it fills a different database.
- `frontend` builds into `backend/staticfiles/` with `frontend/publish.sh`.

## Quick start (local)
Requires Python 3.13 and Node.js.

1. **Seed the database** (creates `backend/db.sqlite3` by default):
   ```
   cd seed
   python3.13 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python seed.py migrate
   python seed.py locations
   python seed.py modalidades
   ```
2. **Run the backend:**
   ```
   cd ../backend
   python3.13 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   export DJANGO_DEBUG=1
   python manage.py createsuperuser
   python manage.py runserver
   ```
   Admin at http://localhost:8000/admin/, API at http://localhost:8000/api/v0/. Add listings in the admin.
3. **Run the frontend:**
   ```
   cd ../frontend
   cp .env.development.example .env.development   # add REACT_APP_GOOGLE_MAPS_API_KEY
   npm install && npm start
   ```

Each folder's README has the details, configuration and tests.

## Configuration and secrets
- Settings come from environment variables; see [`backend/README.md`](backend/README.md).
- Do not commit `.env*` files, `db.sqlite3` or `media/` (all ignored).
- Restrict the Google Maps key by referrer, and rotate any secret that was ever committed to the older repositories.

## Deployment
Not set up yet. The configuration is environment-driven (database, secret key, hosts, media path),
so it can run on a virtual machine with Postgres and a web server in front of Django that serves
`/media/` and `/img/`.
