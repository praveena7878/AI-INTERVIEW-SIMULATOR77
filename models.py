from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True, nullable=True)
    resume_raw = Column(Text, nullable=True)
    resume_json = Column(Text, nullable=True)  # JSON representation of Name, Skills, Projects, Education, Experience
    skills = Column(Text, nullable=True)  # Comma-separated or JSON array of skills
    
    interviews = relationship("Interview", back_populates="user", cascade="all, delete-orphan")

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime(timezone=True), server_default=func.now())
    overall_score = Column(Float, default=0.0)
    technical_score = Column(Float, default=0.0)
    communication_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    behavioral_score = Column(Float, default=0.0)
    status = Column(String, default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED
    difficulty = Column(String, default="EASY")  # EASY, MEDIUM, HARD
    current_question_index = Column(Integer, default=0)
    
    user = relationship("User", back_populates="interviews")
    answers = relationship("Answer", back_populates="interview", cascade="all, delete-orphan")

class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"))
    question = Column(Text)
    answer = Column(Text, nullable=True)
    question_type = Column(String)  # INTRO, TECHNICAL, BEHAVIORAL
    target_skill = Column(String, nullable=True)
    difficulty_level = Column(String)  # EASY, MEDIUM, HARD
    
    # Technical Evaluation
    technical_score = Column(Float, default=0.0)
    clarity = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    feedback = Column(Text, nullable=True)
    
    # Communication Analysis
    grammar_score = Column(Float, default=0.0)
    vocabulary_score = Column(Float, default=0.0)
    fluency_score = Column(Float, default=0.0)
    communication_feedback = Column(Text, nullable=True)
    
    # Behavioral Evaluation (STAR score & feedback)
    behavioral_star_score = Column(Float, default=0.0)
    behavioral_star_feedback = Column(Text, nullable=True)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    interview = relationship("Interview", back_populates="answers")
