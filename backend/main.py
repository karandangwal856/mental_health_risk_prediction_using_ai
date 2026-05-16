from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import joblib
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
import os
import datetime
from typing import List

import models
import schemas
import auth
from database import engine, get_db

# Create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MindCheck AI - Advanced Mental Health Platform")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load existing model
model_path = os.path.join(os.path.dirname(__file__), 'models', 'mental_health_model.pkl')
model = joblib.load(model_path) if os.path.exists(model_path) else None

# --- AUTH ROUTES ---

@app.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# --- DAILY RECORDS ---

@app.post("/daily-records", response_model=schemas.DailyRecordResponse)
def create_daily_record(
    record: schemas.DailyRecordCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_record = models.DailyRecord(**record.model_dump(), user_id=current_user.id)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@app.get("/daily-records", response_model=List[schemas.DailyRecordResponse])
def list_daily_records(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.DailyRecord).filter(models.DailyRecord.user_id == current_user.id).order_by(models.DailyRecord.date.desc()).all()

@app.put("/daily-records/{record_id}", response_model=schemas.DailyRecordResponse)
def update_daily_record(
    record_id: int,
    record: schemas.DailyRecordCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_record = db.query(models.DailyRecord).filter(models.DailyRecord.id == record_id, models.DailyRecord.user_id == current_user.id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    for key, value in record.model_dump().items():
        setattr(db_record, key, value)
    
    db.commit()
    db.refresh(db_record)
    return db_record

# --- SMART AI THERAPIST ---

@app.post("/chat", response_model=schemas.ChatResponse)
def smart_chat(
    request: schemas.ChatRequest,
    current_user: models.User = Depends(auth.get_current_user)
):
    if not request.message.strip():
        return {
            "reply": "I'm here for you, but I didn't catch that. Could you please share what's on your mind?",
            "empathy_score": 0.5,
            "context": "empty_message"
        }
        
    if len(request.message) > 1000:
        return {
            "reply": "That's a lot to take in! I'm listening, but could we try focusing on one part of what's on your mind at a time?",
            "empathy_score": 0.7,
            "context": "long_message"
        }

    message = request.message.lower()
    
    # Context-aware logic
    if "failed" in message or "exam" in message or "score" in message:
        reply = f"I'm sorry to hear about your exam, {current_user.full_name}. Remember that one grade doesn't define your worth or your future. It's okay to feel disappointed, but please be kind to yourself today. What's one small thing you can do to relax right now?"
        context = "academic_stress"
        empathy_score = 0.95
    elif "alone" in message or "lonely" in message or "no one" in message:
        reply = "I hear you, and I want you to know that you're not alone in feeling this way. Loneliness can be really tough, but I'm here to listen. Sometimes reaching out to even one person, or even just sitting in a public space, can help. How long have you been feeling this way?"
        context = "loneliness"
        empathy_score = 0.98
    elif "stress" in message or "work" in message or "pressure" in message:
        reply = "Work pressure can be overwhelming. It sounds like you're carrying a lot on your shoulders. Have you had a chance to take a 5-minute breather today? Our 'Relaxation' section has a great breathing exercise that might help."
        context = "work_stress"
        empathy_score = 0.92
    elif "sad" in message or "depressed" in message or "down" in message:
        reply = "I'm so sorry you're feeling down. It takes a lot of courage to acknowledge these feelings. Please remember that it's okay not to be okay. Have you considered taking our Depression Assessment to get a better understanding of what you're experiencing?"
        context = "low_mood"
        empathy_score = 0.96
    elif "happy" in message or "good" in message or "great" in message:
        reply = "That's wonderful to hear! I'm so glad you're having a good day. It's important to celebrate these positive moments. What's been the best part of your day so far?"
        context = "positive_mood"
        empathy_score = 0.90
    else:
        reply = "I'm here for you. Whether you want to talk about your day, your feelings, or just need a safe space to vent, I'm listening. How are you feeling in this moment?"
        context = "general"
        empathy_score = 0.85
        
    return {
        "reply": reply,
        "empathy_score": empathy_score,
        "context": context
    }

# --- ASSESSMENTS ---

@app.post("/predict-risk")
def predict_risk(
    data: schemas.SurveyData,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Only use original 6 features for the ML model
    model_features = ['age', 'gender', 'family_history', 'work_interference', 'benefits', 'care_options']
    input_data = {k: v for k, v in data.model_dump().items() if k in model_features}
    input_df = pd.DataFrame([input_data])
    
    prediction = int(model.predict(input_df)[0])
    probability = float(model.predict_proba(input_df)[0][1])
    
    recommendation = "High Risk" if prediction == 1 else "Low Risk"
    
    # Save result
    result = models.AssessmentResult(
        type='risk',
        score=probability,
        details=data.model_dump(),
        user_id=current_user.id
    )
    db.add(result)
    db.commit()
    
    return {
        "risk_detected": bool(prediction),
        "risk_probability": probability,
        "recommendation": recommendation
    }

@app.post("/assess-anxiety")
def assess_anxiety(
    data: schemas.AnxietySurveyData,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Simple scoring (GAD-7)
    score = sum(data.model_dump().values())
    
    result = models.AssessmentResult(
        type='anxiety',
        score=float(score),
        details=data.model_dump(),
        user_id=current_user.id
    )
    db.add(result)
    db.commit()
    
    interpretation = "Severe Anxiety" if score >= 15 else "Moderate Anxiety" if score >= 10 else "Mild Anxiety" if score >= 5 else "Minimal Anxiety"
    
    return {"score": score, "interpretation": interpretation}

@app.post("/assess-depression")
def assess_depression(
    data: schemas.DepressionSurveyData,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Simple scoring (PHQ-9)
    score = sum(data.model_dump().values())
    
    result = models.AssessmentResult(
        type='depression',
        score=float(score),
        details=data.model_dump(),
        user_id=current_user.id
    )
    db.add(result)
    db.commit()
    
    interpretation = "Severe Depression" if score >= 20 else "Moderately Severe" if score >= 15 else "Moderate" if score >= 10 else "Mild" if score >= 5 else "Minimal"
    
    return {"score": score, "interpretation": interpretation}

# --- DOCTOR SUGGESTIONS ---

@app.get("/doctors")
def suggest_doctors():
    # Mock Indian Doctor Data
    doctors = [
        {
            "id": 1, 
            "name": "Dr. Sameer Malhotra", 
            "specialty": "Psychiatrist", 
            "city": "Delhi", 
            "experience": "25 years",
            "profile_url": "https://www.maxhealthcare.in/doctor/dr-sameer-malhotra"
        },
        {
            "id": 2, 
            "name": "NIMHANS Bangalore", 
            "specialty": "Mental Health & Neuro Sciences", 
            "city": "Bangalore", 
            "experience": "Premier Institution",
            "profile_url": "https://nimhans.ac.in/"
        },
        {
            "id": 3, 
            "name": "Dr. Anjali Chhabria", 
            "specialty": "Psychotherapist", 
            "city": "Mumbai", 
            "experience": "20 years",
            "profile_url": "https://www.mindtemple.com/dr-anjali-chhabria.html"
        },
        {
            "id": 4, 
            "name": "Dr. Rajiv Gupta", 
            "specialty": "Child Psychiatrist", 
            "city": "Gurugram", 
            "experience": "18 years",
            "profile_url": "https://www.practo.com/gurgaon/doctor/dr-rajiv-gupta-psychiatrist"
        },
        {
            "id": 5, 
            "name": "Fortis Mental Health", 
            "specialty": "Multidisciplinary", 
            "city": "National", 
            "experience": "Hospital Chain",
            "profile_url": "https://www.fortishealthcare.com/speciality/mental-health-and-behavioural-sciences"
        }
    ]
    return doctors

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
