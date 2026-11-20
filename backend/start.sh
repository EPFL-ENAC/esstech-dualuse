#!/bin/sh

# Apply database migrations, load the curated cases, then start the API server.
#
# The cases are defined only in scripts/seed_cases.py. Seeding is idempotent
# and overwrites each case by title, so edit them there, not in the database:
# changes made directly in the database are lost at the next start.
alembic upgrade head
python -m scripts.seed_cases || echo "WARNING: case seeding failed; serving the cases already in the database" >&2

uvicorn --host=0.0.0.0 --timeout-keep-alive=0 api.main:app
