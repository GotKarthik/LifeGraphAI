import os
import json
from transformers import pipeline

# We use a singleton class to lazily load the heavy Transformer models
# only when the Celery worker actually processes a journal.
# This prevents the FastAPI web server from using 1.5GB of RAM needlessly!
class LocalExtractor:
    _sentiment_pipe = None
    _ner_pipe = None
    _emotion_pipe = None
    _topic_pipe = None
    _chat_pipe = None
    
    @classmethod
    def get_sentiment(cls):
        if cls._sentiment_pipe is None:
            print("Loading Local Sentiment Pipeline (distilbert-sst-2)...")
            cls._sentiment_pipe = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        return cls._sentiment_pipe

    @classmethod
    def get_ner(cls):
        if cls._ner_pipe is None:
            print("Loading Local NER Pipeline (bert-base-NER)...")
            cls._ner_pipe = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
        return cls._ner_pipe

    @classmethod
    def get_emotion(cls):
        if cls._emotion_pipe is None:
            print("Loading Local Emotion Pipeline (distilbert-emotion)...")
            cls._emotion_pipe = pipeline("text-classification", model="bhadresh-savani/distilbert-base-uncased-emotion")
        return cls._emotion_pipe

    @classmethod
    def get_topic(cls):
        if cls._topic_pipe is None:
            print("Loading Local Topic Pipeline (zero-shot-classification)...")
            cls._topic_pipe = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")
        return cls._topic_pipe

    @classmethod
    def get_chat(cls):
        if cls._chat_pipe is None:
            print("Loading Local Chat Pipeline (Qwen2.5-1.5B-Instruct)...")
            # We use a lightweight open-source LLM for chat and summaries
            cls._chat_pipe = pipeline("text-generation", model="Qwen/Qwen2.5-1.5B-Instruct", max_new_tokens=512)
        return cls._chat_pipe

def extract_structured_memory_sync(text: str) -> dict:
    """
    100% Offline Extraction Pipeline.
    Replaces Google Gemini entirely with specialized local Transformers.
    """
    result = {
        "entities": [],
        "emotions": [],
        "topics": [],
        "action_items": [],
        "overall_mood_score": 50
    }
    
    # 1. Calculate precise 1-100 Mood Score
    try:
        sent = LocalExtractor.get_sentiment()(text)[0]
        # label is POSITIVE or NEGATIVE, score is a confidence from 0.5 to 1.0
        base = 50
        if sent['label'] == 'POSITIVE':
            # Map 0.5-1.0 confidence to 50-100 score
            base += int((sent['score'] - 0.5) * 100)
        else:
            # Map 0.5-1.0 confidence to 50-0 score
            base -= int((sent['score'] - 0.5) * 100)
        result["overall_mood_score"] = max(1, min(100, base))
    except Exception as e:
        print(f"Local Sentiment error: {e}")

    # 2. Extract People, Organizations, Locations
    try:
        ner_results = LocalExtractor.get_ner()(text)
        entities = set()
        for ent in ner_results:
            if ent['entity_group'] in ['PER', 'LOC', 'ORG']:
                entities.add(ent['word'])
        result["entities"] = list(entities)
    except Exception as e:
        print(f"Local NER error: {e}")

    # 3. Extract primary Emotion
    try:
        emo = LocalExtractor.get_emotion()(text)[0]
        result["emotions"] = [emo['label']]
    except Exception as e:
        print(f"Local Emotion error: {e}")

    # 4. Extract overarching Topics via Zero-Shot Classification
    try:
        candidate_labels = ["work", "relationships", "health", "finance", "hobbies", "personal growth", "travel", "fitness", "family"]
        topic_res = LocalExtractor.get_topic()(text, candidate_labels)
        topics = []
        for label, score in zip(topic_res['labels'], topic_res['scores']):
            # If the model is more than 30% confident the journal is about this topic
            if score > 0.3:
                topics.append(label)
        result["topics"] = topics[:2] # Take top 2
    except Exception as e:
        print(f"Local Topic error: {e}")

    return result
