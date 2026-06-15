from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from api.deps import SessionDep, CurrentUser
from models.journal import Journal
from schemas.journal import JournalCreate, JournalUpdate, JournalResponse
from core.encryption import encrypt_data, decrypt_data

router = APIRouter()

@router.post("/", response_model=JournalResponse)
def create_journal(
    journal_in: JournalCreate,
    db: SessionDep,
    current_user: CurrentUser
):
    ciphertext, nonce = encrypt_data(str(current_user.id), journal_in.content)
    
    db_journal = Journal(
        user_id=current_user.id,
        title=journal_in.title,
        content_encrypted=ciphertext,
        content_nonce=nonce,
        mood=journal_in.mood,
        entry_type=journal_in.entry_type,
    )
    db.add(db_journal)
    db.commit()
    db.refresh(db_journal)
    
    # Trigger memory pipeline
    from worker.tasks import process_journal_pipeline
    process_journal_pipeline.delay(str(db_journal.id), str(current_user.id))
    
    # Decrypt to return in response
    return JournalResponse(
        id=db_journal.id,
        user_id=db_journal.user_id,
        title=db_journal.title,
        mood=db_journal.mood,
        entry_type=db_journal.entry_type,
        processing_status=db_journal.processing_status,
        created_at=db_journal.created_at,
        updated_at=db_journal.updated_at,
        content=journal_in.content
    )

@router.get("/", response_model=List[JournalResponse])
def get_journals(
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100
):
    journals = db.query(Journal).filter(Journal.user_id == current_user.id).order_by(Journal.created_at.desc()).offset(skip).limit(limit).all()
    results = []
    for j in journals:
        decrypted_content = decrypt_data(str(current_user.id), j.content_encrypted, j.content_nonce)
        res = JournalResponse(
            id=j.id,
            user_id=j.user_id,
            title=j.title,
            mood=j.mood,
            entry_type=j.entry_type,
            processing_status=j.processing_status,
            created_at=j.created_at,
            updated_at=j.updated_at,
            content=decrypted_content
        )
        results.append(res)
    return results

@router.get("/{id}", response_model=JournalResponse)
def get_journal(
    id: UUID,
    db: SessionDep,
    current_user: CurrentUser
):
    journal = db.query(Journal).filter(Journal.id == id, Journal.user_id == current_user.id).first()
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")
    
    decrypted_content = decrypt_data(str(current_user.id), journal.content_encrypted, journal.content_nonce)
    return JournalResponse(
        id=journal.id,
        user_id=journal.user_id,
        title=journal.title,
        mood=journal.mood,
        entry_type=journal.entry_type,
        processing_status=journal.processing_status,
        created_at=journal.created_at,
        updated_at=journal.updated_at,
        content=decrypted_content
    )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_journal(
    id: UUID,
    db: SessionDep,
    current_user: CurrentUser
):
    journal = db.query(Journal).filter(Journal.id == id, Journal.user_id == current_user.id).first()
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")
    db.delete(journal)
    db.commit()
