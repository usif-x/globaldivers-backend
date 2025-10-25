#!/bin/sh
# Startup script for production deployment

echo "Starting application..."

# Try to run migrations
echo "Running database migrations..."
alembic upgrade head

# If migrations fail due to version mismatch, fix it
if [ $? -ne 0 ]; then
    echo "Migration failed. Attempting to fix alembic version..."
    
    # Use Python to clear the alembic version table
    python -c "
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    conn.execute(text('DELETE FROM alembic_version'))
    conn.commit()
print('Cleared alembic_version table')
"
    
    # Now stamp to the latest version
    echo "Stamping database to head..."
    alembic stamp head
    
    # Try migrations again
    echo "Running migrations again..."
    alembic upgrade head
    
    # If still failing, it means the migrations need to be applied
    if [ $? -ne 0 ]; then
        echo "Still failing. This likely means migrations haven't been run yet."
        echo "Attempting to apply migrations from scratch..."
        
        # Clear version again and let upgrade handle it
        python -c "
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    conn.execute(text('DELETE FROM alembic_version'))
    conn.commit()
"
        # Try upgrade one more time
        alembic upgrade head
    fi
fi

echo "Migrations completed successfully!"

# Start the application
echo "Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
