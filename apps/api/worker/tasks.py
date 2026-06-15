from celery import shared_task
from core.celery_app import celery_app
from sqlalchemy.orm import Session
from core.database import SessionLocal
from models.journal import Journal, ProcessingStatus
from models.job import JournalProcessingJob
from models.memory import JournalChunk, StructuredMemory
from core.ai import chunk_text, generate_embedding
from core.llm import extract_structured_memory_sync
from core.encryption import decrypt_data
import uuid

@celery_app.task(bind=True, max_retries=10)
def process_journal_pipeline(self, journal_id: str, user_id: str):
    db = SessionLocal()
    try:
        # Create Job tracking
        job = JournalProcessingJob(
            journal_id=journal_id,
            user_id=user_id,
            status="processing",
            step="chunking"
        )
        db.add(job)
        
        journal = db.query(Journal).filter(Journal.id == journal_id).first()
        if not journal:
            raise Exception("Journal not found")
            
        journal.processing_status = ProcessingStatus.PROCESSING.value
        db.commit()

        # Decrypt content
        content = decrypt_data(str(user_id), journal.content_encrypted, journal.content_nonce)
        
        # Clean up any existing data from previous failed runs to make task idempotent
        db.query(JournalChunk).filter(JournalChunk.journal_id == journal_id).delete()
        db.query(StructuredMemory).filter(StructuredMemory.journal_id == journal_id).delete()
        db.commit()
        
        # Step 1: Chunking
        chunks = chunk_text(content)
        
        # Step 2: Embedding & Save Chunks
        job.step = "embedding"
        db.commit()
        
        for idx, chunk_str in enumerate(chunks):
            embedding = generate_embedding(chunk_str)
            db_chunk = JournalChunk(
                journal_id=journal_id,
                user_id=user_id,
                chunk_index=idx,
                content=chunk_str,
                embedding=embedding
            )
            db.add(db_chunk)
        
        db.commit()
        
        # Step 3: Extracting
        job.step = "extracting"
        db.commit()
        
        extracted_data = extract_structured_memory_sync(content)
        
        # Save AI sentiment score to journal
        journal.mood = str(extracted_data.get("overall_mood_score", 50))
        
        structured_memory = StructuredMemory(
            journal_id=journal_id,
            user_id=user_id,
            entities=extracted_data
        )
        db.add(structured_memory)
        db.commit()
        db.refresh(structured_memory)
        
        # Build graph nodes and edges
        from core.graph import process_memory_graph
        process_memory_graph(db, structured_memory)
        
        # Finalize
        journal.processing_status = ProcessingStatus.COMPLETED.value
        job.status = "completed"
        job.step = "done"
        db.commit()

    except Exception as exc:
        db.rollback()
        # Track failure only if we exhausted retries
        if self.request.retries >= self.max_retries:
            job = db.query(JournalProcessingJob).filter(
                JournalProcessingJob.journal_id == journal_id,
                JournalProcessingJob.status == "processing"
            ).first()
            if job:
                job.status = "failed"
                job.error = str(exc)
                
            journal = db.query(Journal).filter(Journal.id == journal_id).first()
            if journal:
                journal.processing_status = ProcessingStatus.FAILED.value
                
            db.commit()
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()
