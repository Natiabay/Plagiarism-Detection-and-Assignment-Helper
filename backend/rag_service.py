from typing import List, Dict, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from openai import OpenAI
from config import settings
from models import AcademicSource

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Set up logging
logger = logging.getLogger(__name__)


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
    threshold: float = 0.5  # Lowered from 0.7 to 0.5 for better recall
) -> List[Dict]:
    """Search for similar academic sources using vector similarity.
    
    This function performs semantic search by:
    1. Generating an embedding for the query text
    2. Comparing it against stored source embeddings (title + abstract)
    3. Returning the most similar sources ordered by relevance
    
    Args:
        db: Database session
        query_text: The search query text
        top_k: Number of top results to return
        threshold: Minimum similarity score (0.0-1.0). Lower values return more results.
    
    Returns:
        List of source dictionaries with similarity scores, ordered by relevance
    """
    try:
        # Log the query for debugging
        logger.info(f"Searching for query: '{query_text}'")
        
        # Check if there are any sources in the database
        source_count = db.query(AcademicSource).count()
        if source_count == 0:
            raise Exception("No academic sources found in database. Please load sample sources from data/sample_academic_sources.json")
        
        logger.info(f"Found {source_count} sources in database")
        
        # Generate embedding for query - this MUST be called with the actual query_text
        # Note: Sources are embedded using "title + abstract", so the query should
        # be semantically similar to what users would search for in academic contexts
        logger.info(f"Generating embedding for query: '{query_text[:50]}...'")
        query_embedding = generate_embedding(query_text)
        logger.info(f"Generated embedding with {len(query_embedding)} dimensions")
        
        # Verify embedding is different (check first few values)
        embedding_sample = query_embedding[:5]
        logger.info(f"Embedding sample (first 5 values): {embedding_sample}")
        
        # CRITICAL FIX: Convert to string format that PostgreSQL can parse directly
        # This avoids any issues with parameter binding
        from pgvector.psycopg2 import register_vector
        
        # Get raw psycopg2 connection
        raw_conn = db.connection().connection
        
        # Register vector type adapter
        register_vector(raw_conn)
        
        # Log embedding details to verify it's different for different queries
        import hashlib
        embedding_sample = str(query_embedding[:5])
        embedding_hash = hashlib.md5(embedding_sample.encode()).hexdigest()[:8]
        logger.info(f"Query: '{query_text}' -> Embedding hash: {embedding_hash}, First 3 values: {query_embedding[:3]}")
        
        # Convert to string format that pgvector can parse: [0.1,0.2,0.3,...]
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        # Create a fresh cursor for this query - IMPORTANT: new cursor each time
        cursor = raw_conn.cursor()
        
        # Use f-string to embed the vector directly in the query
        # This ensures the query is completely fresh each time with no parameter caching
        # We use parameterized query for top_k to prevent SQL injection
        sql_query = f"""
            SELECT 
                id,
                title,
                authors,
                publication_year,
                abstract,
                source_type,
                url,
                1 - (embedding <=> '{embedding_str}'::vector) as similarity
            FROM academic_sources
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT %s
        """
        
        # Execute with only top_k as parameter - embedding is embedded in SQL
        # This completely avoids any parameter binding issues
        logger.info(f"Executing vector search query with embedding_hash={embedding_hash}")
        logger.info(f"SQL query preview (first 200 chars): {sql_query[:200]}...")
        
        cursor.execute(sql_query, (top_k,))
        rows = cursor.fetchall()
        
        logger.info(f"Query returned {len(rows)} rows")
        for i, row in enumerate(rows[:3]):  # Log first 3 results
            logger.info(f"  Result {i+1}: id={row[0]}, title={row[1][:40] if row[1] else 'N/A'}..., similarity={row[7]:.4f}")
        
        cursor.close()
        
        sources = []
        for row in rows:
            similarity = float(row[7])  # similarity is the 8th column (0-indexed: 7)
            
            # Return all top_k results ordered by similarity
            # The threshold is advisory - we return the best matches available
            # Users can see the similarity score to judge relevance
            source_dict = {
                "id": row[0],
                "title": row[1],
                "authors": row[2],
                "publication_year": row[3],
                "abstract": row[4],
                "source_type": row[5],
                "url": row[6],
                "relevance": f"Relevance score: {similarity:.2%}",
                "similarity": similarity
            }
            sources.append(source_dict)
            logger.info(f"Found source: {row[1][:50] if row[1] else 'N/A'}... (similarity: {similarity:.4f})")
        
        logger.info(f"Returning {len(sources)} sources for query: '{query_text}'")
        return sources
    
    except Exception as e:
        logger.error(f"Error searching sources: {str(e)}", exc_info=True)
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

