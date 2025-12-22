from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import httpx
import os
from datetime import timedelta

from config import settings
from database import get_db, Base, engine
from models import Student, Assignment, AnalysisResult
from auth import (
    authenticate_student,
    create_access_token,
    get_current_student,
    get_password_hash
)
from file_processor import extract_text_from_file, count_words
from rag_service import search_similar_sources

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Academic Assignment Helper & Plagiarism Detector",
    description="RAG-powered system for assignment analysis and plagiarism detection",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic schemas
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any


class StudentRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    student_id: Optional[str] = None


class StudentLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AnalysisResponse(BaseModel):
    id: int
    assignment_id: int
    original_summary: Optional[str]
    suggested_sources: Optional[List[Dict[str, Any]]]
    plagiarism_score: Optional[float]
    flagged_sections: Optional[List[Dict[str, Any]]]
    research_suggestions: Optional[str]
    citation_recommendations: Optional[str]
    confidence_score: Optional[float]
    analyzed_at: str


class SourceResponse(BaseModel):
    id: int
    title: str
    authors: Optional[str]
    publication_year: Optional[int]
    abstract: Optional[str]
    source_type: Optional[str]
    url: Optional[str]
    relevance: Optional[str]
    similarity: Optional[float]


# Authentication endpoints
@app.post(f"{settings.API_V1_PREFIX}/auth/register", response_model=TokenResponse)
async def register(student_data: StudentRegister, db: Session = Depends(get_db)):
    """Register a new student account."""
    # Check if email already exists
    existing_student = db.query(Student).filter(Student.email == student_data.email).first()
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new student
    student = Student(
        email=student_data.email,
        password_hash=get_password_hash(student_data.password),
        full_name=student_data.full_name,
        student_id=student_data.student_id
    )
    
    db.add(student)
    db.commit()
    db.refresh(student)
    
    # Create access token
    access_token = create_access_token(data={"sub": student.email})
    
    return TokenResponse(access_token=access_token)


@app.post(f"{settings.API_V1_PREFIX}/auth/login", response_model=TokenResponse)
async def login(credentials: StudentLogin, db: Session = Depends(get_db)):
    """Login and get JWT token."""
    student = authenticate_student(credentials.email, credentials.password, db)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": student.email})
    return TokenResponse(access_token=access_token)


# Assignment upload endpoint
@app.post(f"{settings.API_V1_PREFIX}/upload")
async def upload_assignment(
    file: UploadFile = File(...),
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Upload assignment file and trigger n8n analysis."""
    try:
        # Extract text from file
        text_content = await extract_text_from_file(file)
        word_count = count_words(text_content)
        
        # Save assignment to database
        assignment = Assignment(
            student_id=current_student.id,
            filename=file.filename,
            original_text=text_content,
            word_count=word_count
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        
        # Prepare data for n8n webhook
        webhook_data = {
            "student_id": str(current_student.id),
            "assignment_id": assignment.id,
            "filename": file.filename,
            "assignmentText": text_content
        }
        
        # Call n8n webhook
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    settings.N8N_WEBHOOK_URL,
                    json=webhook_data
                )
                response.raise_for_status()
        except Exception as e:
            # Log error but don't fail the upload
            print(f"Error calling n8n webhook: {str(e)}")
        
        return {
            "message": "Assignment uploaded successfully",
            "assignment_id": assignment.id,
            "filename": file.filename,
            "word_count": word_count,
            "status": "Analysis in progress"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


# Get analysis results
@app.get(f"{settings.API_V1_PREFIX}/analysis/{{analysis_id}}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Retrieve analysis results for an assignment."""
    analysis = db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    # Verify the assignment belongs to the current student
    assignment = db.query(Assignment).filter(Assignment.id == analysis.assignment_id).first()
    if not assignment or assignment.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return AnalysisResponse(
        id=analysis.id,
        assignment_id=analysis.assignment_id,
        original_summary=analysis.original_summary,
        suggested_sources=analysis.suggested_sources,
        plagiarism_score=analysis.plagiarism_score,
        flagged_sections=analysis.flagged_sections,
        research_suggestions=analysis.research_suggestions,
        citation_recommendations=analysis.citation_recommendations,
        confidence_score=analysis.confidence_score,
        analyzed_at=analysis.analyzed_at.isoformat() if analysis.analyzed_at else None
    )


# RAG source search endpoint
@app.get(f"{settings.API_V1_PREFIX}/sources", response_model=List[SourceResponse])
async def search_sources(
    query: str,
    top_k: int = 5,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Search academic sources via RAG."""
    try:
        sources = search_similar_sources(db, query, top_k=top_k)
        return [SourceResponse(**source) for source in sources]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching sources: {str(e)}"
        )


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Academic Assignment Helper"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Academic Assignment Helper & Plagiarism Detector API",
        "version": "1.0.0",
        "docs": "/docs"
    }

