import os
from typing import Optional
from fastapi import UploadFile
import PyPDF2
from docx import Document
import aiofiles


async def extract_text_from_file(file: UploadFile) -> str:
    """Extract text from uploaded file (PDF or DOCX)."""
    # Save file temporarily
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    # Read file content
    content = await file.read()
    
    try:
        if file_extension == '.pdf':
            return extract_text_from_pdf(content)
        elif file_extension in ['.docx', '.doc']:
            return extract_text_from_docx(content)
        else:
            # Try to read as plain text
            return content.decode('utf-8', errors='ignore')
    except Exception as e:
        raise Exception(f"Error extracting text from file: {str(e)}")


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF file."""
    try:
        from io import BytesIO
        pdf_file = BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")


def extract_text_from_docx(docx_content: bytes) -> str:
    """Extract text from DOCX file."""
    try:
        from io import BytesIO
        docx_file = BytesIO(docx_content)
        doc = Document(docx_file)
        
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    except Exception as e:
        raise Exception(f"Error reading DOCX: {str(e)}")


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())

