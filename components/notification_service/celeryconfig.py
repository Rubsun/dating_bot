import os

from components.notification_service.config import load_config

cfg_path = os.getenv('NOTIFICATION_SERVICE_CONFIG_PATH', './components/notification_service/configs/app.toml')
cfg = load_config(cfg_path)

broker_url = cfg.celery.broker_url  # Use Redis as message broker
result_backend = cfg.celery.broker_url  # Store task results

task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'UTC'
enable_utc = True