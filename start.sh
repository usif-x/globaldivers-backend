#!/bin/sh
# Startup script for production deployment

echo "Starting application..."

# Initialize alembic if needed
echo "Checking alembic setup..."
alembic current 2>/dev/null

# If alembic isn't initialized, stamp it to the first migration
if [ $? -ne 0 ]; then
    # For production first-time setup, stamp to the initial migration
    # This marks the database as having the base schema without running the initial migration
    echo "First time setup - stamping to initial migration..."
    alembic stamp c12edb7f2aaa
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head

if [ $? -ne 0 ]; then
    echo "Migration failed! Check the logs."
    exit 1
fi

# Start the application
echo "Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
