#!/bin/bash
set -e

# Initialize Airflow database if not exists
if [ ! -f /opt/airflow/airflow.db ]; then
    echo "Initializing Airflow database..."
    airflow db init
    echo "Database initialized successfully!"
else
    echo "Database already exists, skipping initialization."
fi

# Run the command passed to the container
exec "$@"