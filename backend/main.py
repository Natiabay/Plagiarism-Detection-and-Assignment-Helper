from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
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
    get_password_hash,
    verify_password
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
    password: str  # Will be truncated to 72 bytes if longer (bcrypt limit)
    full_name: Optional[str] = None
    student_id: Optional[str] = None


class StudentLogin(BaseModel):
    email: EmailStr
    password: str


class PasswordReset(BaseModel):
    email: EmailStr
    new_password: str


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


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
    
    # Check if student_id already exists (if provided)
    if student_data.student_id:
        existing_student_id = db.query(Student).filter(Student.student_id == student_data.student_id).first()
        if existing_student_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student ID '{student_data.student_id}' is already registered"
            )
    
    try:
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
    
    except Exception as e:
        db.rollback()
        # Handle database integrity errors
        error_str = str(e).lower()
        if "unique" in error_str or "duplicate" in error_str:
            if "email" in error_str:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            elif "student_id" in error_str:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Student ID '{student_data.student_id}' is already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A record with this information already exists"
                )
        # Re-raise other exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating account: {str(e)}"
        )


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


# OAuth2-compatible token endpoint for Swagger UI
@app.post(f"{settings.API_V1_PREFIX}/auth/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2-compatible token endpoint for Swagger UI authorization.
    Uses 'username' field for email address."""
    student = authenticate_student(form_data.username, form_data.password, db)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": student.email})
    return TokenResponse(access_token=access_token)


# Password reset endpoint (for forgotten passwords)
@app.post(f"{settings.API_V1_PREFIX}/auth/reset-password", response_model=MessageResponse)
async def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
    """Reset password for a student account (for forgotten passwords).
    Note: In production, this should require email verification or other security measures."""
    student = db.query(Student).filter(Student.email == reset_data.email).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    # Validate new password length
    if len(reset_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    try:
        # Update password
        student.password_hash = get_password_hash(reset_data.new_password)
        db.commit()
        db.refresh(student)
        
        return MessageResponse(message="Password reset successfully")
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting password: {str(e)}"
        )


# Password change endpoint (for logged-in users)
@app.post(f"{settings.API_V1_PREFIX}/auth/change-password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Change password for logged-in user (requires old password verification)."""
    # Verify old password
    if not verify_password(password_data.old_password, current_student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password"
        )
    
    # Validate new password length
    if len(password_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Check if new password is different from old password
    if verify_password(password_data.new_password, current_student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    try:
        # Update password
        current_student.password_hash = get_password_hash(password_data.new_password)
        db.commit()
        db.refresh(current_student)
        
        return MessageResponse(message="Password changed successfully")
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error changing password: {str(e)}"
        )


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
            "student_email": current_student.email,
            "teacher_email": settings.TEACHER_EMAIL,
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
                print(f"✅ Successfully called n8n webhook: {settings.N8N_WEBHOOK_URL}")
        except httpx.HTTPStatusError as e:
            # Log detailed error but don't fail the upload
            print(f"❌ Error calling n8n webhook: HTTP {e.response.status_code} - {e.response.text}")
            print(f"   URL: {settings.N8N_WEBHOOK_URL}")
        except Exception as e:
            # Log error but don't fail the upload
            print(f"❌ Error calling n8n webhook: {str(e)}")
            print(f"   URL: {settings.N8N_WEBHOOK_URL}")
        
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


# Get analysis results by analysis ID (required endpoint)
@app.get(f"{settings.API_V1_PREFIX}/analysis/{{analysis_id}}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Retrieve analysis results by analysis ID."""
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


# Get analysis results by assignment ID (more convenient)
@app.get(f"{settings.API_V1_PREFIX}/assignments/{{assignment_id}}/analysis", response_model=AnalysisResponse)
async def get_analysis_by_assignment(
    assignment_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Retrieve analysis results for an assignment by assignment_id.
    
    This endpoint is more convenient than using analysis_id since you get assignment_id
    immediately after uploading. The analysis is created by the n8n workflow.
    """
    # Verify the assignment belongs to the current student
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    if assignment.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get the latest analysis for this assignment (n8n may create multiple, get most recent)
    analysis = db.query(AnalysisResult).filter(
        AnalysisResult.assignment_id == assignment_id
    ).order_by(AnalysisResult.analyzed_at.desc()).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found. The assignment may still be processing. Please wait a few moments and try again."
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

