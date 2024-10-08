#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
until pg_isready -h postgres -p 5432 -U postgres; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

# Wait for the specific database to be created
until PGPASSWORD="$POSTGRES_PASSWORD" psql -h postgres -U postgres -d postgres -c "SELECT 1 FROM pg_database WHERE datname = 'yahoo_search_engine_rt';" | grep -q 1; do
  echo "Waiting for database yahoo_search_engine_rt to be created..."
  sleep 2
done

echo "Migrations applied - starting service"
exec "$@"
