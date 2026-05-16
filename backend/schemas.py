from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class DailyRecordBase(BaseModel):
    mood: int
    note: Optional[str] = None
    checklist: Optional[List[Dict[str, Any]]] = None # List of tasks with completed status

class DailyRecordCreate(DailyRecordBase):
    pass

class DailyRecordResponse(DailyRecordBase):
    id: int
    date: datetime
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    empathy_score: float
    context: str

class AssessmentBase(BaseModel):
    type: str
    score: float
    details: Dict[str, Any]

class AssessmentCreate(AssessmentBase):
    pass

class AssessmentResponse(AssessmentBase):
    id: int
    date: datetime
    class Config:
        from_attributes = True

class SurveyData(BaseModel):
    age: int
    gender: int
    family_history: int
    work_interference: int
    benefits: int
    care_options: int
    wellness_program: Optional[int] = 0
    seek_help: Optional[int] = 0
    anonymity: Optional[int] = 0
    leave: Optional[int] = 0

class AnxietySurveyData(BaseModel):
    feeling_nervous: int # 0-3
    not_being_able_to_stop_worrying: int
    worrying_too_much: int
    trouble_relaxing: int
    being_restless: int
    becoming_easily_annoyed: int
    feeling_afraid: int
    concentration: Optional[int] = 0
    sleep_impact: Optional[int] = 0
    social_impact: Optional[int] = 0

class DepressionSurveyData(BaseModel):
    little_interest: int # 0-3
    feeling_down: int
    trouble_sleeping: int
    feeling_tired: int
    poor_appetite: int
    feeling_bad_about_self: int
    trouble_concentrating: int
    moving_slowly: int
    thoughts_of_harm: int
    hopelessness: Optional[int] = 0
    decision_making: Optional[int] = 0
    withdrawal: Optional[int] = 0
