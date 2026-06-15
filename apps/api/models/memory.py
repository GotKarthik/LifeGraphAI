import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from core.database import Base

class JournalChunk(Base):
    __tablename__ = "journal_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_id = Column(UUID(as_uuid=True), ForeignKey("journals.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(String, nullable=False)
    embedding = Column(Vector(1024), nullable=True) # Will use HNSW index in alembic
    chunk_index = Column(Integer, nullable=False)

class StructuredMemory(Base):
    __tablename__ = "structured_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_id = Column(UUID(as_uuid=True), ForeignKey("journals.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    entities = Column(JSONB, nullable=False)
    extracted_at = Column(DateTime, default=datetime.utcnow)

class Summary(Base):
    __tablename__ = "summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    period_type = Column(String, nullable=False) # e.g. "daily", "weekly"
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    content = Column(String, nullable=False)
    embedding = Column(Vector(1024), nullable=True)

class MemoryNode(Base):
    __tablename__ = "memory_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    node_type = Column(String, nullable=False) # person, goal, place, etc
    label = Column(String, nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=True)

class MemoryEdge(Base):
    __tablename__ = "memory_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_node_id = Column(UUID(as_uuid=True), ForeignKey("memory_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(UUID(as_uuid=True), ForeignKey("memory_nodes.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String, nullable=False)
    weight = Column(Float, default=1.0)
    metadata_ = Column("metadata", JSONB, nullable=True)
