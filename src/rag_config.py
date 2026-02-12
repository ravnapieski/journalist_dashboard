import os
from src.config import DB_FOLDER

# --- PATHS ---
VECTOR_DB_DIR = os.path.join(DB_FOLDER, "vector_stores", "chroma_db")
os.makedirs(VECTOR_DB_DIR, exist_ok=True)

# --- MODEL CONFIGURATION ---
RAG_SETTINGS = {
    "chat_model": "meta-llama/llama-4-scout-17b-16e-instruct",
    "grader_model": "groq/compound-mini", 
    "embedding_model": "intfloat/multilingual-e5-base", 
    "k_retrieval": 5,
    "similarity_threshold": 0.3,
    "chat_temperature": 0.3,
}

# --- PROMPTS ---
SYSTEM_PROMPT = """You are a specialized Editorial Assistant for a Journalist Dashboard.
Your role is to analyze a journalist's past articles (provided as context) and answer questions to help produce better future journalism.

CONTEXT INFORMATION:
The context provided to you consists of news articles written in FINNISH.
The user will ask questions in ENGLISH.

INSTRUCTIONS:
1. Answer the user's question based ONLY on the provided context.
2. If the answer is not in the context, state that you cannot answer based on the available articles.
3. You must answer in English
4. CITATIONS: You MUST cite the specific article title when referencing information. Format citations as [Title].
"""

QA_PROMPT_TEMPLATE = """
Context:
{context}

User Question: {question}

Answer:
"""