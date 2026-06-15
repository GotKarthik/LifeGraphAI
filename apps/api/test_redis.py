from core.celery_app import celery_app
from worker.tasks import process_journal_pipeline
print(celery_app.conf.broker_url)
print("Sending test task...")
res = process_journal_pipeline.delay("test", "test")
print("Task ID:", res.id)
