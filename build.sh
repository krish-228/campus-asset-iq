#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Safely load fixture without crashing build if records already exist
if [ -f "campus_data.json" ]; then
    python manage.py loaddata campus_data.json || echo "Fixtures already loaded or skipped."
fi

