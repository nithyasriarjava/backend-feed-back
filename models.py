import enum
# IMPORT UPDATE: Change 'text' to 'text as sa_text'
from sqlalchemy import Column, String, Text, Enum, TIMESTAMP, text as sa_text, BigInteger, Integer
from database import Base

class StatusEnum(str, enum.Enum):
    pending = "pending"
    done = "done"
    failed = "failed"

class CategoryEnum(str, enum.Enum):
    bug = "bug"
    feature_request = "feature_request"
    complaint = "complaint"
    praise = "praise"

class SentimentEnum(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_email = Column(String, nullable=False)    
    # This is the column name that caused the conflict
    text = Column(Text, nullable=False)
    
    category = Column(Enum(CategoryEnum), nullable=True)
    sentiment = Column(Enum(SentimentEnum), nullable=True)
    summary = Column(String(500), nullable=True)
    
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.pending)
    error_message = Column(Text, nullable=True)
    
    # FIX: Use 'sa_text' instead of 'text' here
    created_at = Column(TIMESTAMP, server_default=sa_text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, server_default=sa_text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255)) # Hashed password