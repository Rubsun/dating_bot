from celery import Celery
from celery.schedules import schedule

# Initialize Celery
app = Celery('project')
app.config_from_object('components.notification_service.celeryconfig')

# Configure beat schedule
app.conf.beat_schedule = {
    'run-my-task-every-hour': {
        'task': 'components.notification_service.poll_likes.hourly_task',
        'schedule': schedule(run_every=5),  # Runs at the start of every hour
    },
}

app.conf.timezone = 'UTC'


@app.task
def hourly_task():
    # Your task logic here
    pass
