# Atbarcelona-React

React front-end for the AtBarcelona stack.

## Development
```
cp .env.development.example .env.development   # then add REACT_APP_GOOGLE_MAPS_API_KEY
npm install && npm start
```
`REACT_APP_API_URL` selects the backend (`http://localhost:8000/api` by default).
`./publish.sh` builds and copies the result into `../backend/staticfiles/`.
