from core.database import SessionLocal
from models.journal import Journal
from worker.tasks import process_journal_pipeline

db = SessionLocal()
pending = db.query(Journal).filter(Journal.processing_status == "pending").all()
for j in pending:
    print(f"Re-queuing {j.id}")
    process_journal_pipeline.delay(str(j.id), str(j.user_id))
db.close()
