from sqlalchemy import Column, Integer, String, Text, Float, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from database import Base


class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    student_id = Column(String, unique=True, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    assignments = relationship("Assignment", back_populates="student", cascade="all, delete-orphan")


class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), index=True)
    filename = Column(String, nullable=False)
    original_text = Column(Text)
    topic = Column(String)
    academic_level = Column(String)
    word_count = Column(Integer)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())
    
    student = relationship("Student", back_populates="assignments")
    analysis_results = relationship("AnalysisResult", back_populates="assignment", cascade="all, delete-orphan")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    original_summary = Column(Text)
    suggested_sources = Column(JSONB)
    plagiarism_score = Column(Float)
    flagged_sections = Column(JSONB)
    research_suggestions = Column(Text)
    citation_recommendations = Column(Text)
    confidence_score = Column(Float)
    analyzed_at = Column(TIMESTAMP, server_default=func.now())
    
    assignment = relationship("Assignment", back_populates="analysis_results")


class AcademicSource(Base):
    __tablename__ = "academic_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    authors = Column(String)
    publication_year = Column(Integer)
    abstract = Column(Text)
    full_text = Column(Text)
    source_type = Column(String)  # 'paper', 'textbook', 'course_material'
    url = Column(String)
    embedding = Column(Vector(1536))
    created_at = Column(TIMESTAMP, server_default=func.now())

