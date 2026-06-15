from fastapi import APIRouter
from pydantic import BaseModel
from api.deps import SessionDep, CurrentUser
from core.retrieval import hybrid_search

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

@router.post("/search")
def search_memory(
    request: SearchRequest,
    db: SessionDep,
    current_user: CurrentUser
):
    results = hybrid_search(db, str(current_user.id), request.query, request.top_k)
    return results

class AskRequest(BaseModel):
    query: str

@router.post("/ask")
def ask_memory(
    request: AskRequest,
    db: SessionDep,
    current_user: CurrentUser
):
    from core.agent import run_reflection_agent
    results = run_reflection_agent(db, str(current_user.id), request.query)
    return results

@router.get("/graph")
def get_graph(db: SessionDep, current_user: CurrentUser):
    from core.graph import get_user_graph
    return get_user_graph(db, str(current_user.id))

@router.get("/timeline")
def get_timeline(db: SessionDep, current_user: CurrentUser):
    from models.journal import Journal
    journals = db.query(Journal).filter(Journal.user_id == current_user.id).order_by(Journal.created_at.asc()).all()
    
    timeline = []
    for j in journals:
        timeline.append({
            "id": str(j.id),
            "date": j.created_at.isoformat(),
            "mood": j.mood,
            "title": j.title
        })
    return timeline

@router.post("/summary")
def generate_summary(db: SessionDep, current_user: CurrentUser):
    from models.journal import Journal
    from core.encryption import decrypt_data
    from core.summary import generate_summary_sync
    
    journals = db.query(Journal).filter(Journal.user_id == current_user.id).order_by(Journal.created_at.desc()).limit(10).all()
    
    texts = []
    for j in journals:
        content = decrypt_data(str(current_user.id), j.content_encrypted, j.content_nonce)
        texts.append(f"Title: {j.title}\nDate: {j.created_at}\nMood: {j.mood}\nContent: {content}")
        
    summary = generate_summary_sync(texts)
    return {"summary": summary}
