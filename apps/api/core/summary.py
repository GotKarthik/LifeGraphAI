from core.llm import LocalExtractor

def generate_summary_sync(text_chunks: list[str]) -> str:
    combined = "\n---\n".join(text_chunks[:10])
    prompt = f"""
    Based on the following journal entries, write a concise, reflective summary of the user's journey.
    Highlight recurrent themes, emotional state, and progress towards goals. Do not output anything other than the summary.
    
    Entries:
    {combined}
    """
    
    try:
        chat_pipe = LocalExtractor.get_chat()
        
        # Qwen/ChatML prompt format
        system_prompt = "You are a thoughtful journal summarizer."
        qwen_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt.strip()}<|im_end|>\n<|im_start|>assistant\n"
        
        response = chat_pipe(qwen_prompt, max_new_tokens=300, return_full_text=False)
        return response[0]["generated_text"].strip()
    except Exception as e:
        print("Error generating summary:", e)
        return "Unable to generate summary at this time."
