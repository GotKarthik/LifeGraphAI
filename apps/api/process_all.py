from core.database import SessionLocal
from models.journal import Journal
from worker.tasks import process_journal_pipeline
from celery.app.task import Context

db = SessionLocal()
pending = db.query(Journal).filter(Journal.processing_status.in_(["pending", "failed"])).all()
db.close()

for j in pending:
    print(f"Processing {j.id}...")
    try:
        # Call the actual underlying function synchronously
        process_journal_pipeline.apply(args=(str(j.id), str(j.user_id))).get()
        print(f"Success for {j.id}")
    except Exception as e:
        print(f"Failed {j.id}: {e}")
