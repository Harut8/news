#!/bin/bash
echo "Applying database migrations !!!!!!!!!"
alembic upgrade head
echo "Applied database migrations !!!!!!!!!"
exec "$@"
