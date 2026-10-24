# frontend

React front end for the AtBarcelona listings site: search, results, listing detail and map.

React 17, TypeScript, Redux Toolkit.

## Development
```
cd frontend
cp .env.development.example .env.development   # then add REACT_APP_GOOGLE_MAPS_API_KEY
npm install
npm start
```
The app expects the [backend](../backend/README.md) running (default `http://localhost:8000/api`).

## Configuration
| Variable | Meaning |
|---|---|
| `REACT_APP_API_URL` | Backend API base URL. Default `http://localhost:8000/api`; `.env.production.example` uses `/api` (same origin). |
| `REACT_APP_GOOGLE_MAPS_API_KEY` | Google Maps key. Restrict it by HTTP referrer in Google Cloud. |

`.env.development` and `.env.production` hold the key and are not tracked by git; copy the `.example` files.

## Build and publish
```
./publish.sh
```
Runs `npm run build` and copies `build/` into `../backend/staticfiles/`, where Django serves it.
The compiled bundle in `backend/staticfiles/static/js/` is committed, so rebuild after changing the source.

## API types
`src/features/interfaces.ts` describes the API responses (listing, detail tables, locations,
modalidades, rental conditions, reservation request). Keep it in step with the backend serializers.
The detail page does not yet show every section the API returns; see [`../TODO.md`](../TODO.md).
