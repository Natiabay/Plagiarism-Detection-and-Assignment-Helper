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
        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        raise Exception(f"Error generating embedding: {str(e)}")


def search_similar_sources(
    db: Session,
    query_text: str,
    top_k: int = 5,
    threshold: float = 0.7
) -> List[Dict]:
    """Search for similar academic sources using vector similarity."""
    try:
        # Generate embedding for query
        query_embedding = generate_embedding(query_text)
        
        # Convert to PostgreSQL array format
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        # Query using cosine similarity
        query = text("""
            SELECT 
                id,
                title,
                authors,
                publication_year,
                abstract,
                source_type,
                url,
                1 - (embedding <=> :embedding::vector) as similarity
            FROM academic_sources
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :embedding::vector
            LIMIT :top_k
        """)
        
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

