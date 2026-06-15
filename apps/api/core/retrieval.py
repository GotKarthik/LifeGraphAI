from sqlalchemy.orm import Session
from sqlalchemy import text
from models.memory import JournalChunk, StructuredMemory
from models.journal import Journal
from core.ai import generate_embedding
import json

def hybrid_search(db: Session, user_id: str, query: str, top_k: int = 5):
    # Generate query embedding
    query_embedding = generate_embedding(query)
    
    # 1. Semantic Search using pgvector
    # Order by L2 distance (<->)
    chunks = db.query(JournalChunk).filter(
        JournalChunk.user_id == user_id
    ).order_by(
        JournalChunk.embedding.l2_distance(query_embedding)
    ).limit(top_k).all()
    
    # 2. Extract keywords for JSONB search
    keywords = [word.lower() for word in query.split() if len(word) > 3]
    
    # JSONB search (topics, entities)
    jsonb_results = []
    if keywords:
        for kw in keywords:
            memories = db.query(StructuredMemory).filter(
                StructuredMemory.user_id == user_id,
                (StructuredMemory.entities['entities'].contains([kw])) |
                (StructuredMemory.entities['topics'].contains([kw]))
            ).limit(top_k).all()
            jsonb_results.extend(memories)
            
    # Compile results with journal metadata
    semantic_chunks_with_meta = []
    for c in chunks:
        journal = db.query(Journal).filter(Journal.id == c.journal_id).first()
        if journal:
            semantic_chunks_with_meta.append({
                "id": str(c.id), 
                "journal_id": str(c.journal_id), 
                "title": journal.title,
                "date": journal.created_at.isoformat(),
                "content": c.content
            })
            
    structured_hits_with_meta = []
    for m in jsonb_results:
        journal = db.query(Journal).filter(Journal.id == m.journal_id).first()
        if journal:
            structured_hits_with_meta.append({
                "id": str(m.id), 
                "journal_id": str(m.journal_id), 
                "title": journal.title,
                "date": journal.created_at.isoformat(),
                "entities": m.entities.get("entities", []), 
                "topics": m.entities.get("topics", [])
            })

    results = {
        "semantic_chunks": semantic_chunks_with_meta,
        "structured_hits": structured_hits_with_meta
    }
    
    return results
