from sqlalchemy.orm import Session
from . import models, schemas
import json

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_name(db: Session, name: str):
    return db.query(models.User).filter(models.User.name == name).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_resume(db: Session, user_id: int, resume_raw: str, resume_json: dict, skills: list):
    db_user = get_user(db, user_id)
    if db_user:
        db_user.resume_raw = resume_raw
        db_user.resume_json = json.dumps(resume_json)
        db_user.skills = json.dumps(skills)
        db.commit()
        db.refresh(db_user)
    return db_user

def get_interview(db: Session, interview_id: int):
    return db.query(models.Interview).filter(models.Interview.id == interview_id).first()

def get_interviews_by_user(db: Session, user_id: int):
    return db.query(models.Interview).filter(models.Interview.user_id == user_id).order_by(models.Interview.date.desc()).all()

def create_interview(db: Session, interview: schemas.InterviewCreate):
    db_interview = models.Interview(
        user_id=interview.user_id,
        difficulty=interview.difficulty,
        status="IN_PROGRESS",
        current_question_index=0
    )
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    return db_interview

def update_interview(db: Session, interview_id: int, **kwargs):
    db_interview = get_interview(db, interview_id)
    if db_interview:
        for key, value in kwargs.items():
            setattr(db_interview, key, value)
        db.commit()
        db.refresh(db_interview)
    return db_interview

def create_answer(db: Session, interview_id: int, answer_data: schemas.AnswerBase):
    db_answer = models.Answer(
        interview_id=interview_id,
        question=answer_data.question,
        answer=answer_data.answer,
        question_type=answer_data.question_type,
        difficulty_level=answer_data.difficulty_level,
        target_skill=answer_data.target_skill
    )
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    return db_answer

def update_answer_evaluation(db: Session, answer_id: int, evaluation: schemas.AnswerEvaluation):
    db_answer = db.query(models.Answer).filter(models.Answer.id == answer_id).first()
    if db_answer:
        db_answer.technical_score = evaluation.technical_score
        db_answer.clarity = evaluation.clarity
        db_answer.confidence = evaluation.confidence
        db_answer.feedback = evaluation.feedback
        
        # Communication
        db_answer.grammar_score = evaluation.grammar_score
        db_answer.vocabulary_score = evaluation.vocabulary_score
        db_answer.fluency_score = evaluation.fluency_score
        db_answer.communication_feedback = evaluation.communication_feedback
        
        # Behavioral
        db_answer.behavioral_star_score = evaluation.behavioral_star_score
        db_answer.behavioral_star_feedback = evaluation.behavioral_star_feedback
        
        db.commit()
        db.refresh(db_answer)
    return db_answer
