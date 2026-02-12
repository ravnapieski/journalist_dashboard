import sqlite3
import os
import shutil
from typing import List, Dict, Any

from langchain_community.document_loaders import DataFrameLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import pandas as pd

from src.config import DB_PATH
from src.rag_config import (
    VECTOR_DB_DIR, 
    RAG_SETTINGS, 
    SYSTEM_PROMPT, 
    QA_PROMPT_TEMPLATE
)

class RAGIngestion:
    """Handles fetching journalist articles from the database, 
    splitting them into text chunks, and ingesting them into the vector store."""
    def __init__(self):
        print(f"Loading embedding model: {RAG_SETTINGS['embedding_model']}...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=RAG_SETTINGS['embedding_model'],
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        self.vector_db = Chroma(
            persist_directory=VECTOR_DB_DIR,
            embedding_function=self.embeddings,
            collection_name="journalist_articles"
        )

    def fetch_articles_from_db(self, journalist_id: str) -> pd.DataFrame:
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT id, title, content, url, published_date FROM articles WHERE journalist_id = ?"
        df = pd.read_sql_query(query, conn, params=(journalist_id,))
        conn.close()
        return df

    def ingest_journalist_data(self, journalist_id: str):
        print(f"Starting ingestion for Journalist ID: {journalist_id}")
        df = self.fetch_articles_from_db(journalist_id)
        if df.empty:
            print("No articles found.")
            return False

        # Prepare Text Splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        documents = []
        for _, row in df.iterrows():
            # Create content with title for better context
            full_text = f"Title: {row['title']}\n\nContent:\n{row['content']}"
            
            metadatas = {
                "article_id": str(row['id']),
                "journalist_id": str(journalist_id),
                "title": row['title'],
                "url": row['url'],
                "published_date": row['published_date']
            }
            documents.extend(text_splitter.create_documents([full_text], metadatas=[metadatas]))

        print(f"Generated {len(documents)} chunks from {len(df)} articles.")

        # Clear old data for this journalist
        try:
            results = self.vector_db.get(where={"journalist_id": journalist_id})
            if results['ids']:
                print(f"Removing {len(results['ids'])} old chunks...")
                self.vector_db.delete(ids=results['ids'])
        except Exception as e:
            print(f"Metadata filter cleanup skipped: {e}")

        if documents:
            self.vector_db.add_documents(documents)
            print("Ingestion complete. Data persisted.")
            return True
        return False

class RAGChain:
    """Manages retrieval-augmented generation:
    retrieves relevant article chunks, formats the prompt, 
    and generates answers using ChatGroq."""
    def __init__(self):
        # init embeddinggs
        self.embeddings = HuggingFaceEmbeddings(
            model_name=RAG_SETTINGS['embedding_model'],
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # load da vector db
        self.vector_db = Chroma(
            persist_directory=VECTOR_DB_DIR,
            embedding_function=self.embeddings,
            collection_name="journalist_articles"
        )

        # init groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        self.llm = ChatGroq(
            temperature=RAG_SETTINGS['chat_temperature'],
            model_name=RAG_SETTINGS['chat_model'],
            api_key=api_key
        )

    def format_docs(self, docs):
        """Format retrieved documents for the prompt."""
        formatted_string = ""
        for i, doc in enumerate(docs):
            formatted_string += f"\n--- Article {i+1}: {doc.metadata.get('title', 'Unknown')} ---\n"
            formatted_string += doc.page_content
            formatted_string += "\n"
        return formatted_string

    def get_response(self, query: str, journalist_id: str) -> Dict[str, Any]:
        """
        Main RAG function:
        1. Retrieve relevant chunks for specific journalist.
        2. Format prompt.
        3. Generate answer.
        """
        
        # only get chunks belonging to this specific journalist
        retriever = self.vector_db.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": RAG_SETTINGS['k_retrieval'],
                "filter": {"journalist_id": journalist_id} 
            }
        )
        
        # get docs
        print(f"Retrieving context for: '{query}'...")
        retrieved_docs = retriever.invoke(query)
        
        if not retrieved_docs:
            return {
                "answer": "I couldn't find any relevant articles for this journalist in the database.",
                "sources": []
            }

        # build prompt like bob the builder
        context_text = self.format_docs(retrieved_docs)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", QA_PROMPT_TEMPLATE.format(context=context_text, question=query))
        ])

        print("Generating answer with Llama...")
        chain = prompt | self.llm | StrOutputParser()
        answer = chain.invoke({})

        sources = list(set([doc.metadata.get('title') for doc in retrieved_docs]))
        
        return {
            "answer": answer,
            "sources": sources,
            "context_used": context_text # Debugging helper
        }

# --- TEST BLOCK ---
if __name__ == "__main__":
    from dotenv import load_dotenv # type: ignore
    load_dotenv() # Load .env for API Key

    # Hardcoded test
    TEST_JOURNALIST_ID = "56-74-1533" # my yle journalist id :D
    TEST_QUERY = "What does this journalist write about? Give short answer."

    print(f"--- RAG TEST: {TEST_QUERY} ---")
    
    try:
        rag = RAGChain()
        result = rag.get_response(TEST_QUERY, TEST_JOURNALIST_ID)
        
        print("\n=== ANSWER ===")
        print(result['answer'])
        print("\n=== SOURCES ===")
        print(result['sources'])
        
    except Exception as e:
        print(f"Error: {e}")