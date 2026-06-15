from sqlalchemy.orm import Session
from core.config import settings
from core.retrieval import hybrid_search
from core.llm import LocalExtractor
from models.user import User
from google import genai

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def run_reflection_agent(db: Session, user_id: str, query: str) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    full_name = user.full_name if user and user.full_name else "User"
    bio_text = f"\n{user.bio}\n" if user and user.bio else "\n"

    # 1. Retrieve context using hybrid search
    # Top 6 matches provides a focused context window to eliminate noise
    search_results = hybrid_search(db, user_id, query, top_k=6)
    
    # 2. Format context into a readable string for the LLM
    context_blocks = []
    
    # Add Semantic Chunks
    if search_results["semantic_chunks"]:
        context_blocks.append("--- EXCERPTS FROM JOURNALS ---")
        for chunk in search_results["semantic_chunks"]:
            date_str = chunk["date"][:10]  # Just YYYY-MM-DD
            title = chunk["title"] or "Untitled"
            content = chunk["content"]
            jid = chunk["journal_id"]
            context_blocks.append(f"[Journal ID: {jid}] On {date_str} ({title}):\n{content}\n")
            
    # Add Structured Graph/Entity Hits
    if search_results["structured_hits"]:
        context_blocks.append("--- STRUCTURED METADATA (Topics & Entities) ---")
        for hit in search_results["structured_hits"]:
            date_str = hit["date"][:10]
            title = hit["title"] or "Untitled"
            entities = ", ".join(hit["entities"])
            topics = ", ".join(hit["topics"])
            jid = hit["journal_id"]
            context_blocks.append(f"[Journal ID: {jid}] On {date_str} ({title}) -> Topics: {topics} | Entities: {entities}")

    context_text = "\n".join(context_blocks)
    
    if not context_text.strip():
        context_text = "No journal entries found matching the query."

    # 3. Iterative RAG (Self-Correction Loop)
    chat_pipe = LocalExtractor.get_chat()
    
    # PASS 1: Analysis (Chain of Thought)
    analysis_system = """You are an analytical engine. Given the user's QUESTION and the provided CONTEXT, think step-by-step.
CRITICAL INSTRUCTION: The CONTEXT consists of excerpts from the user's own personal journal. When the user asks about "I", "me", or "my", they are referring to the author of the journal entries.
1. Extract explicit facts from the CONTEXT that answer the QUESTION.
2. If the answer is not explicitly stated, analyze the text for implicit patterns, behaviors, and subtext that provide a nuanced answer. 
3. Note specific Journal IDs that support your analysis.
Do NOT output the final response to the user. Just output your logical analysis."""

    user_prompt_1 = f"CONTEXT:\n{context_text}\n\nQUESTION: {query}"
    
    messages_1 = [
        {"role": "system", "content": analysis_system},
        {"role": "user", "content": user_prompt_1}
    ]
    prompt_1 = chat_pipe.tokenizer.apply_chat_template(messages_1, tokenize=False, add_generation_prompt=True)
    
    try:
        res_1 = chat_pipe(prompt_1, max_new_tokens=256, return_full_text=False, temperature=0.1, do_sample=True, repetition_penalty=1.1)
        raw_1 = res_1[0]["generated_text"]
        analysis_text = raw_1[len(prompt_1):].strip() if raw_1.startswith(prompt_1) else raw_1.strip()
        print(f"--- INTERNAL ANALYSIS ---\n{analysis_text}\n-------------------------")
        
        # PASS 2: Synthesis with Gemini
        synth_system = f"""You are a personal reflection assistant for {full_name}.{bio_text}
Always respond in second person — 'you felt', 'you wrote', 'your entries show'. 
Never refer to the user as 'the narrator', 'the author', or 'the person'.
HARD RULES:
1. Never give advice or emotional coaching unless explicitly asked.
2. Base your answer ONLY on the provided context. If not in context, say so.
3. Never reference previous conversations — each query is independent.
4. Reflect {full_name}'s personality/voice if apparent from their writing, but avoid overly repetitive or tautological phrasing.
5. Be concise and natural in your answer. Do NOT include inline citations (like [Journal ID: X]) in your text."""

        user_prompt_2 = f"""CONTEXT:
{context_text}

QUESTION: {query}

EXTRACTED FACTS (from analysis):
{analysis_text}

Write the final response now."""
        
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt_2,
                config=genai.types.GenerateContentConfig(
                    system_instruction=synth_system,
                ),
            )
            answer = response.text
        except Exception as e:
            print("Error in Gemini synthesis:", e)
            answer = "I'm sorry, I encountered an error while synthesizing your response with Gemini."

    except Exception as e:
        print("Error in local iterative generation:", e)
        answer = "I'm sorry, I encountered an error while trying to think about this!"
    
    # 5. Extract unique sources used to return to the frontend
    sources = []
    used_ids = set()
    
    for chunk in search_results["semantic_chunks"]:
        if chunk["journal_id"] not in used_ids:
            sources.append({
                "id": chunk["journal_id"],
                "title": chunk["title"],
                "date": chunk["date"]
            })
            used_ids.add(chunk["journal_id"])
            
    for hit in search_results["structured_hits"]:
        if hit["journal_id"] not in used_ids:
            sources.append({
                "id": hit["journal_id"],
                "title": hit["title"],
                "date": hit["date"]
            })
            used_ids.add(hit["journal_id"])

    return {
        "answer": answer,
        "sources": sources
    }
