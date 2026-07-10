from pydantic import BaseModel, EmailStr


from typing import Optional
from models import StatusEnum, CategoryEnum, SentimentEnum

# User ulla anupra Auth credentials
class AuthData(BaseModel):
    email: EmailStr
    password: str

# User submit pandra input
class FeedbackCreate(BaseModel):
    text: str

# GET request-la namma anupra exact JSON shape
class FeedbackResponse(BaseModel):
    id: int
    text: str
    category: Optional[CategoryEnum]
    sentiment: Optional[SentimentEnum]
    summary: Optional[str]
    status: StatusEnum
    
    class Config:
        from_attributes = True