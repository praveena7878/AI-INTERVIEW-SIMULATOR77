from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    skills: Optional[List[str]] = []
    resume_json: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class AnswerBase(BaseModel):
    question: str
    answer: str
    question_type: str
    difficulty_level: str
    target_skill: Optional[str] = None

class AnswerCreate(BaseModel):
    answer: str

class AnswerEvaluation(BaseModel):
    technical_score: float
    clarity: float
    confidence: float
    feedback: str
    
    # Communication
    grammar_score: float
    vocabulary_score: float
    fluency_score: float
    communication_feedback: str
    
    # Behavioral
    behavioral_star_score: float
    behavioral_star_feedback: str

class AnswerResponse(AnswerBase):
    id: int
    interview_id: int
    technical_score: float
    clarity: float
    confidence: float
    feedback: Optional[str] = None
    grammar_score: float
    vocabulary_score: float
    fluency_score: float
    communication_feedback: Optional[str] = None
    behavioral_star_score: float
    behavioral_star_feedback: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class InterviewBase(BaseModel):
    difficulty: str = "EASY"

class InterviewCreate(InterviewBase):
    user_id: int

class InterviewResponse(BaseModel):
    id: int
    user_id: int
    date: datetime
    overall_score: float
    technical_score: float
    communication_score: float
    confidence_score: float
    behavioral_score: float
    status: str
    difficulty: str
    current_question_index: int

    class Config:
        from_attributes = True

class InterviewSessionDetail(InterviewResponse):
    answers: List[AnswerResponse] = []
    user: UserResponse

    class Config:
        from_attributes = True

class ResumeParseResponse(BaseModel):
    name: str
    skills: List[str]
    projects: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    experience: List[Dict[str, Any]] = []

class QuestionResponse(BaseModel):
    question: str
    question_type: str  # INTRO, TECHNICAL, BEHAVIORAL
    difficulty_level: str  # EASY, MEDIUM, HARD
    target_skill: Optional[str] = None

class ReportStrengthWeakness(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    recommended_topics: List[str]

class FinalReportResponse(BaseModel):
    interview_id: int
    date: datetime
    overall_score: float
    technical_score: float
    communication_score: float
    confidence_score: float
    behavioral_score: float
    strengths: List[str]
    weaknesses: List[str]
    recommended_topics: List[str]
    answer_evaluations: List[Dict[str, Any]]
