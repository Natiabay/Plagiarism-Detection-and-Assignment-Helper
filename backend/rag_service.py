from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from openai import OpenAI
from config import settings
from models import AcademicSource

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using OpenAI."""
    try:
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "":
            raise Exception("OPENAI_API_KEY is not set. Please configure it in your .env file.")
        
        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg or "OPENAI_API_KEY" in error_msg:
            raise Exception(f"OpenAI API key not configured: {error_msg}")
        raise Exception(f"Error generating embedding: {error_msg}")


def search_similar_sources(
    db: Session,
    query_text: str,
    top_k: int = 5,
    threshold: float = 0.7
) -> List[Dict]:
    """Search for similar academic sources using vector similarity."""
    try:
        # Check if there are any sources in the database
        source_count = db.query(AcademicSource).count()
        if source_count == 0:
            raise Exception("No academic sources found in database. Please load sample sources from data/sample_academic_sources.json")
        
        # Generate embedding for query
        query_embedding = generate_embedding(query_text)
        
        # Query using cosine similarity with proper vector casting
        query = text("""
            SELECT 
                id,
                title,
                authors,
                publication_year,
                abstract,
                source_type,
                url,
                1 - (embedding <=> CAST(:embedding AS vector)) as similarity
            FROM academic_sources
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """)
        
        # Convert embedding list to string format for PostgreSQL
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        result = db.execute(
            query,
            {
                "embedding": embedding_str,
                "top_k": top_k
            }
        )
        
        sources = []
        for row in result:
            if row.similarity >= threshold:
                sources.append({
                    "id": row.id,
                    "title": row.title,
                    "authors": row.authors,
                    "publication_year": row.publication_year,
                    "abstract": row.abstract,
                    "source_type": row.source_type,
                    "url": row.url,
                    "relevance": f"Relevance score: {row.similarity:.2%}",
                    "similarity": float(row.similarity)
                })
        
        return sources
    
    except Exception as e:
        raise Exception(f"Error searching sources: {str(e)}")


def add_academic_source(
    db: Session,
    title: str,
    authors: Optional[str] = None,
    publication_year: Optional[int] = None,
    abstract: Optional[str] = None,
    full_text: Optional[str] = None,
    source_type: str = "paper",
    url: Optional[str] = None
) -> AcademicSource:
    """Add a new academic source with embedding."""
    try:
        # Generate embedding from title + abstract
        text_for_embedding = f"{title}"
        if abstract:
            text_for_embedding += f" {abstract}"
        
        embedding = generate_embedding(text_for_embedding)
        
        # Create source
        source = AcademicSource(
            title=title,
            authors=authors,
            publication_year=publication_year,
            abstract=abstract,
            full_text=full_text,
            source_type=source_type,
            url=url,
            embedding=embedding
        )
        
        db.add(source)
        db.commit()
        db.refresh(source)
        
        return source
    
    except Exception as e:
        db.rollback()
        raise Exception(f"Error adding source: {str(e)}")

