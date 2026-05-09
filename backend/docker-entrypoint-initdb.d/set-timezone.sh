#!/usr/bin/env bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	ALTER SYSTEM SET timezone = 'Africa/Lagos';
  SELECT pg_reload_conf();
EOSQL
