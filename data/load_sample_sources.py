"""
Script to load sample academic sources into the database with embeddings.
Run this after the database is set up.
"""
import json
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import settings
from backend.rag_service import add_academic_source

# Load environment variables
load_dotenv()

def load_sources():
    """Load sample academic sources from JSON file."""
    # Create database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Load JSON file
        json_path = os.path.join(os.path.dirname(__file__), "sample_academic_sources.json")
        with open(json_path, 'r', encoding='utf-8') as f:
            sources = json.load(f)
        
        print(f"Loading {len(sources)} academic sources...")
        
        for i, source_data in enumerate(sources, 1):
            try:
                source = add_academic_source(
                    db=db,
                    title=source_data['title'],
                    authors=source_data.get('authors'),
                    publication_year=source_data.get('publication_year'),
                    abstract=source_data.get('abstract'),
                    full_text=source_data.get('full_text'),
                    source_type=source_data.get('source_type', 'paper'),
                    url=source_data.get('url')
                )
                print(f"✓ Loaded source {i}/{len(sources)}: {source.title}")
            except Exception as e:
                print(f"✗ Error loading source {i}: {str(e)}")
        
        print(f"\n✓ Successfully loaded {len(sources)} academic sources!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    load_sources()

