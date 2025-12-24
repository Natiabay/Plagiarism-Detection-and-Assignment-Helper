from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from config import settings
from database import get_db
from models import Student

# Password hashing - use bcrypt directly to avoid passlib detection issues
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme - use token endpoint for Swagger UI compatibility
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/token")


def _truncate_password(password: str) -> str:
    """Truncate password to 72 bytes (bcrypt limit)."""
    # Encode to bytes, truncate to 72 bytes, then decode back
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return password_bytes.decode('utf-8', errors='ignore')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt directly."""
    # Truncate password to match bcrypt's 72-byte limit
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Use bcrypt directly
    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
    except Exception:
        # Fallback to passlib for old hashes
        return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt directly."""
    # Truncate password to match bcrypt's 72-byte limit
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Use bcrypt directly to avoid passlib detection issues
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire, "role": "student"})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def authenticate_student(email: str, password: str, db: Session) -> Optional[Student]:
    """Authenticate a student by email and password."""
    student = db.query(Student).filter(Student.email == email).first()
    if not student:
        return None
    if not verify_password(password, student.password_hash):
        return None
    return student


async def get_current_student(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Student:
    """Get the current authenticated student from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    student = db.query(Student).filter(Student.email == email).first()
    if student is None:
        raise credentials_exception
    
    return student

