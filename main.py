import os
import sys

# Dynamic environment repair for Windows system PATH issues
if sys.platform == 'win32':
    if 'SystemRoot' not in os.environ:
        os.environ['SystemRoot'] = 'C:\\Windows'
    system32_path = 'C:\\Windows\\System32'
    windows_path = 'C:\\Windows'
    wbem_path = 'C:\\Windows\\System32\\Wbem'
    current_path = os.environ.get('PATH', '')
    paths = [p.strip() for p in current_path.split(';') if p.strip()]
    dirty = False
    if system32_path not in paths:
        paths.append(system32_path)
        dirty = True
    if windows_path not in paths:
        paths.append(windows_path)
        dirty = True
    if wbem_path not in paths:
        paths.append(wbem_path)
        dirty = True
    if dirty:
        os.environ['PATH'] = ';'.join(paths)

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime

from .database import engine, Base, get_db
from . import crud, schemas, models, llm, resume_parser, interview as engine_logic

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Interview Simulator API")

# Configure CORS for local React app development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local ease of use
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "AI Interview Simulator API is running successfully.",
        "documentation": "/docs"
    }

def get_api_key(x_gemini_api_key: Optional[str] = Header(None)) -> str:
    """Helper to extract Gemini API key from headers or default to env."""
    from .config import settings
    key = x_gemini_api_key or settings.GEMINI_API_KEY
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Gemini API Key is missing. Please set it in backend .env or enter it in the top bar of the application."
        )
    # Log masked key to backend console for debugging
    masked_key = f"{key[:6]}...{key[-4:]}" if len(key) > 10 else "invalid (too short)"
    logger.info(f"Using Gemini API Key: {masked_key} (length: {len(key)})")
    return key

@app.post("/api/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registers a new user or returns an existing user by name."""
    db_user = crud.get_user_by_name(db, user.name)
    if not db_user:
        db_user = crud.create_user(db, user)
    
    # Parse resume JSON if exists
    resume_dict = {}
    if db_user.resume_json:
        try:
            resume_dict = json.loads(db_user.resume_json)
        except Exception:
            pass
            
    skills_list = []
    if db_user.skills:
        try:
            skills_list = json.loads(db_user.skills)
        except Exception:
            pass
            
    return schemas.UserResponse(
        id=db_user.id,
        name=db_user.name,
        email=db_user.email,
        skills=skills_list,
        resume_json=resume_dict
    )

@app.post("/api/upload-resume/{user_id}", response_model=schemas.ResumeParseResponse)
async def upload_resume(
    user_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Uploads a PDF resume, parses its text, extracts structured skills via Gemini, and saves it."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF resume uploads are supported.")
        
    file_bytes = await file.read()
    raw_text = resume_parser.extract_text_from_pdf(file_bytes)
    
    if not raw_text:
        raise HTTPException(status_code=400, detail="Could not extract text from the uploaded PDF resume.")
        
    try:
        # Structure using Gemini
        parsed_resume = llm.parse_resume(raw_text, api_key=api_key)
        skills = parsed_resume.get("skills", [])
        
        if not skills:
            # Fallback if no skills parsed
            skills = ["Python", "JavaScript", "Software Engineering", "SQL"]
            parsed_resume["skills"] = skills
            
        crud.update_user_resume(db, user_id, raw_text, parsed_resume, skills)
        return schemas.ResumeParseResponse(
            name=parsed_resume.get("name", "Unknown"),
            skills=skills,
            projects=parsed_resume.get("projects", []),
            education=parsed_resume.get("education", []),
            experience=parsed_resume.get("experience", [])
        )
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        raise HTTPException(status_code=500, detail=f"Resume extraction failed: {str(e)}")

@app.post("/api/start-interview")
def start_interview(
    session_data: schemas.InterviewCreate, 
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Starts a new interview session and generates the first (introductory) question."""
    db_user = crud.get_user(db, session_data.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Create interview record
    db_interview = crud.create_interview(db, session_data)
    
    # Parse skills
    skills = []
    if db_user.skills:
        try:
            skills = json.loads(db_user.skills)
        except Exception:
            pass
            
    # Parse resume json
    resume_json = {}
    if db_user.resume_json:
        try:
            resume_json = json.loads(db_user.resume_json)
        except Exception:
            pass
            
    # Generate intro question
    try:
        first_question = llm.generate_question(
            resume_json=resume_json,
            question_type="INTRO",
            difficulty=db_interview.difficulty,
            target_skill=None,
            history=[],
            api_key=api_key
        )
        
        # Save first question as a pending answer record in DB
        crud.create_answer(
            db=db,
            interview_id=db_interview.id,
            answer_data=schemas.AnswerBase(
                question=first_question,
                answer="",
                question_type="INTRO",
                difficulty_level=db_interview.difficulty,
                target_skill=None
            )
        )
        
        return {
            "interview_id": db_interview.id,
            "question": first_question,
            "question_type": "INTRO",
            "difficulty_level": db_interview.difficulty,
            "current_question_index": 0,
            "total_questions": engine_logic.TOTAL_QUESTIONS
        }
    except Exception as e:
        logger.error(f"Failed to generate first question: {e}")
        raise HTTPException(status_code=500, detail=f"Interview initiation failed: {str(e)}")

@app.get("/api/interview/{interview_id}/question")
def get_current_question(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """Retrieves the current active question for an ongoing interview."""
    db_interview = crud.get_interview(db, interview_id)
    if not db_interview:
        raise HTTPException(status_code=404, detail="Interview not found")
        
    if db_interview.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="This interview has already been completed.")
        
    # Get the active unanswered answer record
    active_answer = db.query(models.Answer).filter(
        models.Answer.interview_id == interview_id,
        (models.Answer.answer == "") | (models.Answer.answer == None)
    ).order_by(models.Answer.id.desc()).first()
    
    if not active_answer:
        raise HTTPException(status_code=400, detail="No active question found for this interview.")
        
    return {
        "interview_id": interview_id,
        "question": active_answer.question,
        "question_type": active_answer.question_type,
        "difficulty_level": active_answer.difficulty_level,
        "current_question_index": db_interview.current_question_index,
        "total_questions": engine_logic.TOTAL_QUESTIONS,
        "target_skill": active_answer.target_skill
    }

@app.post("/api/interview/{interview_id}/answer")
def submit_answer(
    interview_id: int,
    answer_payload: schemas.AnswerCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Submits the answer for the current question, evaluates it, adjusts difficulty,

    and returns the next question or completes the interview.
    """
    db_interview = crud.get_interview(db, interview_id)
    if not db_interview:
        raise HTTPException(status_code=404, detail="Interview not found")
        
    if db_interview.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="This interview has already been completed.")
        
    # Get the active unanswered answer record
    active_answer = db.query(models.Answer).filter(
        models.Answer.interview_id == interview_id,
        (models.Answer.answer == "") | (models.Answer.answer == None)
    ).order_by(models.Answer.id.desc()).first()
    
    if not active_answer:
        raise HTTPException(status_code=400, detail="No active question found for this interview.")
        
    # Update active answer with user response
    active_answer.answer = answer_payload.answer
    db.commit()
    
    # Evaluate answer via Gemini
    try:
        eval_result = llm.evaluate_answer(
            question=active_answer.question,
            answer=active_answer.answer,
            question_type=active_answer.question_type,
            target_skill=active_answer.target_skill,
            api_key=api_key
        )
        
        # Save evaluation to db
        eval_schema = schemas.AnswerEvaluation(**eval_result)
        crud.update_answer_evaluation(db, active_answer.id, eval_schema)
    except Exception as e:
        logger.error(f"Failed evaluating answer: {e}")
        # Default safety scores if evaluation crashes
        eval_schema = schemas.AnswerEvaluation(
            technical_score=60.0, clarity=60.0, confidence=60.0,
            feedback=f"Evaluation encountered a temporary error: {str(e)}",
            grammar_score=70.0, vocabulary_score=70.0, fluency_score=70.0,
            communication_feedback="Could not evaluate grammar.",
            behavioral_star_score=60.0, behavioral_star_feedback="Could not evaluate behavioral STAR structures."
        )
        crud.update_answer_evaluation(db, active_answer.id, eval_schema)
        
    # Increment question index
    next_index = db_interview.current_question_index + 1
    crud.update_interview(db, interview_id, current_question_index=next_index)
    
    db_user = crud.get_user(db, db_interview.user_id)
    skills = json.loads(db_user.skills) if db_user.skills else []
    resume_json = json.loads(db_user.resume_json) if db_user.resume_json else {}
    
    # Check if interview is finished
    if next_index >= engine_logic.TOTAL_QUESTIONS:
        # Wrap up interview
        answers = db.query(models.Answer).filter(models.Answer.interview_id == interview_id).all()
        scores = engine_logic.calculate_final_scores(answers)
        
        # Generate summary strengths, weaknesses, and topics
        try:
            eval_list = [
                {
                    "question": a.question,
                    "answer": a.answer,
                    "question_type": a.question_type,
                    "target_skill": a.target_skill,
                    "technical_score": a.technical_score,
                    "feedback": a.feedback,
                    "communication_feedback": a.communication_feedback
                } for a in answers
            ]
            summary = llm.generate_report_summary(eval_list, skills, api_key=api_key)
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            summary = {
                "strengths": ["Completed the interview session"],
                "weaknesses": ["Further analysis needed"],
                "recommended_topics": ["Review general interview performance"]
            }
            
        # Save summary details to DB
        crud.update_interview(
            db, 
            interview_id, 
            status="COMPLETED",
            overall_score=scores["overall_score"],
            technical_score=scores["technical_score"],
            communication_score=scores["communication_score"],
            confidence_score=scores["confidence_score"],
            behavioral_score=scores["behavioral_score"]
        )
        
        # Save strengths/weaknesses and topics (we can structure it in a metadata file or just save in the summary response)
        # For SQLite database simplicity, we return them directly, and the report endpoint generates them or extracts them.
        # Let's save a summary file or store it in interview details. We can store it as JSON string inside models if we want,
        # but returning it directly works beautifully. Let's write them to the final report dashboard.
        
        return {
            "status": "COMPLETED",
            "scores": scores,
            "summary": summary
        }
    else:
        # Adapt difficulty based on last answer score
        new_difficulty = engine_logic.adjust_difficulty(
            current_difficulty=db_interview.difficulty,
            last_score=eval_schema.technical_score
        )
        
        # Save updated difficulty
        crud.update_interview(db, interview_id, difficulty=new_difficulty)
        
        # Determine next question details
        next_type, next_skill = engine_logic.get_next_question_type_and_skill(next_index, skills)
        
        # Fetch history
        past_answers = db.query(models.Answer).filter(models.Answer.interview_id == interview_id).all()
        history = [{"question": a.question, "answer": a.answer} for a in past_answers]
        
        # Generate the next question
        try:
            next_question = llm.generate_question(
                resume_json=resume_json,
                question_type=next_type,
                difficulty=new_difficulty,
                target_skill=next_skill,
                history=history,
                api_key=api_key
            )
            
            # Save the next question
            crud.create_answer(
                db=db,
                interview_id=interview_id,
                answer_data=schemas.AnswerBase(
                    question=next_question,
                    answer="",
                    question_type=next_type,
                    difficulty_level=new_difficulty,
                    target_skill=next_skill
                )
            )
            
            return {
                "status": "IN_PROGRESS",
                "question": next_question,
                "question_type": next_type,
                "difficulty_level": new_difficulty,
                "current_question_index": next_index,
                "total_questions": engine_logic.TOTAL_QUESTIONS,
                "last_evaluation": {
                    "technical_score": eval_schema.technical_score,
                    "clarity": eval_schema.clarity,
                    "confidence": eval_schema.confidence,
                    "feedback": eval_schema.feedback,
                    "grammar": eval_schema.grammar_score,
                    "vocabulary": eval_schema.vocabulary_score,
                    "fluency": eval_schema.fluency_score,
                    "communication_feedback": eval_schema.communication_feedback,
                    "behavioral_star_score": eval_schema.behavioral_star_score,
                    "behavioral_star_feedback": eval_schema.behavioral_star_feedback
                }
            }
        except Exception as e:
            logger.error(f"Failed to generate next question: {e}")
            raise HTTPException(status_code=500, detail=f"Failed generating next question: {str(e)}")

@app.get("/api/interview/{interview_id}/report", response_model=schemas.FinalReportResponse)
def get_interview_report(
    interview_id: int, 
    db: Session = Depends(get_db),
    x_gemini_api_key: Optional[str] = Header(None)
):
    """Generates and retrieves the final comprehensive performance report."""
    db_interview = crud.get_interview(db, interview_id)
    if not db_interview:
        raise HTTPException(status_code=404, detail="Interview not found")
        
    if db_interview.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Interview is still in progress.")
        
    db_user = crud.get_user(db, db_interview.user_id)
    skills = json.loads(db_user.skills) if db_user.skills else []
    
    answers = db.query(models.Answer).filter(models.Answer.interview_id == interview_id).all()
    
    # Generate summary feedback using LLM
    try:
        # Use provided key or settings
        from .config import settings
        key = x_gemini_api_key or settings.GEMINI_API_KEY
        
        eval_list = [
            {
                "question": a.question,
                "answer": a.answer,
                "question_type": a.question_type,
                "target_skill": a.target_skill,
                "technical_score": a.technical_score,
                "feedback": a.feedback,
                "communication_feedback": a.communication_feedback
            } for a in answers
        ]
        summary = llm.generate_report_summary(eval_list, skills, api_key=key)
    except Exception as e:
        logger.error(f"Failed generating report summary: {e}")
        summary = {
            "strengths": ["Communication skills", "Basic concepts"],
            "weaknesses": ["Detailed technical depth"],
            "recommended_topics": ["Review specific project concepts"]
        }
        
    answer_evals = []
    for a in answers:
        answer_evals.append({
            "id": a.id,
            "question": a.question,
            "answer": a.answer,
            "question_type": a.question_type,
            "target_skill": a.target_skill,
            "difficulty_level": a.difficulty_level,
            "technical_score": a.technical_score,
            "clarity": a.clarity,
            "confidence": a.confidence,
            "feedback": a.feedback,
            "grammar_score": a.grammar_score,
            "vocabulary_score": a.vocabulary_score,
            "fluency_score": a.fluency_score,
            "communication_feedback": a.communication_feedback,
            "behavioral_star_score": a.behavioral_star_score,
            "behavioral_star_feedback": a.behavioral_star_feedback,
            "timestamp": a.timestamp
        })
        
    return schemas.FinalReportResponse(
        interview_id=db_interview.id,
        date=db_interview.date,
        overall_score=db_interview.overall_score,
        technical_score=db_interview.technical_score,
        communication_score=db_interview.communication_score,
        confidence_score=db_interview.confidence_score,
        behavioral_score=db_interview.behavioral_score,
        strengths=summary.get("strengths", []),
        weaknesses=summary.get("weaknesses", []),
        recommended_topics=summary.get("recommended_topics", []),
        answer_evaluations=answer_evals
    )

@app.get("/api/user/{user_id}/history", response_model=List[schemas.InterviewResponse])
def get_user_history(user_id: int, db: Session = Depends(get_db)):
    """Retrieves all previous interviews for a user."""
    interviews = crud.get_interviews_by_user(db, user_id)
    return interviews

@app.get("/api/user/{user_id}/trends")
def get_user_trends(user_id: int, db: Session = Depends(get_db)):
    """Retrieves trend data for dashboards."""
    interviews = db.query(models.Interview).filter(
        models.Interview.user_id == user_id,
        models.Interview.status == "COMPLETED"
    ).order_by(models.Interview.date.asc()).all()
    
    trends = []
    for idx, i in enumerate(interviews):
        trends.append({
            "attempt": f"Attempt {idx + 1}",
            "date": i.date.strftime("%Y-%m-%d"),
            "overall": i.overall_score,
            "technical": i.technical_score,
            "communication": i.communication_score,
            "confidence": i.confidence_score,
            "behavioral": i.behavioral_score
        })
    return trends
