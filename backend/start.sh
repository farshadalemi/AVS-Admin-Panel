#!/bin/bash

# Exit on any error
set -e

echo "Starting AVS Admin Panel Backend..."

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "Database is ready!"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Initialize database with default data
echo "Initializing database..."
python -m app.initial_data

# Start the application
echo "Starting FastAPI application..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
