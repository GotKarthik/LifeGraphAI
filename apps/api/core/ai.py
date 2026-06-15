from sentence_transformers import SentenceTransformer
import tiktoken
from core.config import settings

embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)

def generate_embedding(text: str) -> list[float]:
    return embedding_model.encode(text, normalize_embeddings=True).tolist()

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    
    chunks = []
    i = 0
    while i < len(tokens):
        chunk_tokens = tokens[i : i + chunk_size]
        chunks.append(enc.decode(chunk_tokens))
        i += chunk_size - overlap
    return chunks
