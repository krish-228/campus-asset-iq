#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

if [ -n "$DATABASE_URL" ]; then
    python manage.py migrate --noinput
    python manage.py loaddata campus_data.json || true
fi
