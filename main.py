import os
import jwt

from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import List

from database import engine, get_db, SessionLocal
import models
import schemas
from gemini_service import process_feedback_with_ai


# ==============================
# Initialize App & Database
# ==============================

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://feed-back123.netlify.app",
        "https://agent-6a5089da833f51a37a0--frontend-feedback.netlify.app",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

JWT_SECRET = os.getenv("JWT_SECRET")

if not JWT_SECRET:
    raise ValueError(
        "JWT_SECRET environment variable not set."
    )


# ==============================
# JWT Authentication
# ==============================

def get_current_user(
    authorization: str = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid token"
        )

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"]
        )

        return payload.get("sub")

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


# ==============================
# Root
# ==============================

@app.get("/")
def read_root():
    return {
        "message": "Backend is running successfully!"
    }

@app.get("/models")
def list_models():
    models_list = []

    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            models_list.append(m.name)

    return models_list

# ==============================
# Signup
# ==============================

@app.post("/auth/signup")
def signup(
    user: schemas.AuthData,
    db: Session = Depends(get_db)
):
    existing_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = pwd_context.hash(user.password)

    db_user = models.User(
        email=user.email,
        password=hashed_password
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    token = jwt.encode(
        {"sub": db_user.email},
        JWT_SECRET,
        algorithm="HS256"
    )

    return {
        "token": token
    }


# ==============================
# Login
# ==============================

@app.post("/auth/login")
def login(
    user: schemas.AuthData,
    db: Session = Depends(get_db)
):

    db_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not pwd_context.verify(
        user.password,
        db_user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = jwt.encode(
        {"sub": db_user.email},
        JWT_SECRET,
        algorithm="HS256"
    )

    return {
        "message": "Login successful",
        "token": token
    }


# ==============================
# Create Feedback
# ==============================

@app.post("/feedback")
def create_feedback(
    feedback: schemas.FeedbackCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_email: str = Depends(get_current_user)
):

    new_feedback = models.Feedback(
        user_email=user_email,
        text=feedback.text,
        status=models.StatusEnum.pending
    )

    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)

    bg_db_session = SessionLocal()

    background_tasks.add_task(
        process_feedback_with_ai,
        new_feedback.id,
        feedback.text,
        bg_db_session
    )

    return {
        "id": new_feedback.id,
        "text": new_feedback.text,
        "status": new_feedback.status.value
    }


# ==============================
# Get Feedback
# ==============================

@app.get(
    "/feedback",
    response_model=List[schemas.FeedbackResponse]
)
def get_feedback(
    db: Session = Depends(get_db),
    user_email: str = Depends(get_current_user)
):

    return db.query(models.Feedback).filter(
        models.Feedback.user_email == user_email
    ).all()


# ==============================
# Delete Feedback
# ==============================

@app.delete("/feedback/{id}")
def delete_feedback(
    id: int,
    db: Session = Depends(get_db),
    user_email: str = Depends(get_current_user)
):

    feedback = db.query(models.Feedback).filter(
        models.Feedback.id == id,
        models.Feedback.user_email == user_email
    ).first()

    if not feedback:
        raise HTTPException(
            status_code=404,
            detail="Feedback not found"
        )

    db.delete(feedback)
    db.commit()

    return {
        "message": "Deleted successfully"
    }