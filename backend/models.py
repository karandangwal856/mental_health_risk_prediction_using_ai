from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    
    records = relationship("DailyRecord", back_populates="owner")
    assessments = relationship("AssessmentResult", back_populates="owner")

class DailyRecord(Base):
    __tablename__ = "daily_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    mood = Column(Integer) # 1-5 scale
    note = Column(String, nullable=True)
    checklist = Column(JSON, nullable=True) # Mental hygiene checklist state
    user_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="records")

class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String) # 'risk', 'anxiety', 'depression', 'stress'
    score = Column(Float)
    details = Column(JSON)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="assessments")
