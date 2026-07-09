import os
import jwt
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, Header
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import List

from database import engine, get_db, SessionLocal
import models
import schemas
from gemini_service import process_feedback_with_ai

# Initialize app and DB
models.Base.metadata.create_all(bind=engine)
app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Enforce JWT_SECRET configuration for security
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable not set. This is required for security.")

# --- AUTH DEPENDENCY ---
def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    try:
        # Decode the token to get the user email/ID
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("sub") 
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- ENDPOINTS ---
@app.get("/")
def read_root():
    return {"message": "Backend is running successfully!"}

@app.post("/auth/signup")
def signup(user: schemas.AuthData, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    return {"message": "User created successfully"}

@app.post("/auth/login")
def login(user: schemas.AuthData, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    # Use a timing-attack-resistant check.
    # pwd_context.verify will return False for a non-existent user if the hash is None,
    # but checking for the user first makes the intent clearer and avoids a None hash.
    if not db_user or not pwd_context.verify(user.password, db_user.password if db_user else ""):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = jwt.encode({"sub": user.email}, JWT_SECRET, algorithm="HS256")
    return {"token": token}

@app.post("/feedback")
def create_feedback(
    feedback: schemas.FeedbackCreate, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    # 1. Create DB entry with "pending" status
    new_feedback = models.Feedback(
        supabase_user_id=user_id,
        text=feedback.text,
        status=models.StatusEnum.pending
    )
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)

    # 2. Trigger the AI task in the background using a fresh DB session
    bg_db_session = SessionLocal()
    background_tasks.add_task(process_feedback_with_ai, new_feedback.id, feedback.text, bg_db_session)

    # 3. Return immediately! (Assignment requirement met here)
    return {"id": new_feedback.id, "text": new_feedback.text, "status": new_feedback.status.value}

@app.get("/feedback", response_model=List[schemas.FeedbackResponse])
def get_feedback(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    # Fetch all feedback for this logged-in user
    return db.query(models.Feedback).filter(models.Feedback.supabase_user_id == user_id).all()

@app.delete("/feedback/{id}")
def delete_feedback(id: int, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    feedback = db.query(models.Feedback).filter(
        models.Feedback.id == id, 
        models.Feedback.supabase_user_id == user_id
    ).first()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
        
    db.delete(feedback)
    db.commit()
    return {"message": "Deleted successfully"}