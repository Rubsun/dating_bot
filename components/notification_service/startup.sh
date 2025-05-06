echo "Starting services.."

uv run python -m components.notification_service.poll_matches &
uv run celery -A components.notification_service.poll_likes beat --loglevel=info &
uv run celery -A components.notification_service.poll_likes worker --loglevel=info
