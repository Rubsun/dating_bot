from celery import Celery
from celery.schedules import schedule

from components.matching_service.repositories import LikeMatchRepository

# Initialize Celery
app = Celery('project')
app.config_from_object('components.notification_service.celeryconfig')

# Configure beat schedule
app.conf.beat_schedule = {
    'run-my-task-every-hour': {
        'task': 'components.notification_service.poll_likes.minutely_poll_likes_task',
        'schedule': schedule(run_every=60),  # Runs at the start of every hour
    },
}

app.conf.timezone = 'UTC'


@app.task
def minutely_poll_likes_task():
    # Your task logic here
    repo = LikeMatchRepository()
