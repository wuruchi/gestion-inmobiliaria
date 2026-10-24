#!/bin/sh
# Build the frontend and copy it into the Django project's staticfiles.
set -e
npm run build
cp -r build/* ../backend/staticfiles/
