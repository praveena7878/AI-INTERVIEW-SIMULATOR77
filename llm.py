from google import genai
from google.genai import types
import json
import logging
from typing import Dict, Any, List, Optional
from .config import settings

logger = logging.getLogger(__name__)

def get_client(api_key: str = "") -> genai.Client:
    """Creates a new Google GenAI client using the provided key or settings key."""
    key = api_key or settings.GEMINI_API_KEY
    if not key:
        raise ValueError("Gemini API Key is missing. Please set it in settings or provide it in the request.")
    return genai.Client(api_key=key)

def generate_content_with_fallback(
    client: genai.Client, 
    contents: Any, 
    config: Any = None
) -> Any:
    """Helper that attempts generation with a list of model candidates.
    
    If one model is not supported or not found for the user's project scope, 
    it tries alternative models (like gemini-2.5-flash or gemini-2.0-flash) 
    automatically to prevent runtime crashes.
    """
    models_to_try = ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    
    # Try the default configured model first if it's not in the list
    default_model = settings.GEMINI_MODEL
    if default_model not in models_to_try:
        models_to_try.insert(0, default_model)
        
    last_error = None
    for model_name in models_to_try:
        try:
            logger.info(f"Attempting Gemini generation with model: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            logger.info(f"Gemini generation successful with model: {model_name}")
            return response
        except Exception as e:
            last_error = e
            err_msg = str(e).lower()
            # If the model is not found, not supported, experiencing high demand (503), or rate-limited (429), try fallback
            if ("not found" in err_msg or "404" in err_msg or "not supported" in err_msg or 
                "unavailable" in err_msg or "503" in err_msg or "exhausted" in err_msg or "429" in err_msg):
                logger.warning(f"Model {model_name} failed ({e}). Trying next fallback model...")
                continue
            else:
                raise e
                
    # If all candidate models fail, raise the final error
    raise last_error

def parse_json_safely(text: str) -> Dict[str, Any]:
    """Helper to strip markdown tags and parse JSON safely."""
    clean_text = text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {clean_text}. Error: {e}")
        return {}

def parse_resume(resume_text: str, api_key: str = "") -> Dict[str, Any]:
    """Uses Gemini to parse Name, Skills, Education, Experience, and Projects from resume text."""
    client = get_client(api_key)
    
    prompt = f"""
    You are an expert resume parsing engine. Analyze the following resume raw text and extract structured information.
    Format your response as a valid JSON object matching this schema:
    {{
        "name": "Candidate Name (or Unknown if not found)",
        "skills": ["Skill1", "Skill2", "Skill3", ...],
        "projects": [
            {{
                "title": "Project Title",
                "technologies": ["Tech1", "Tech2"],
                "description": "Short description of the project"
            }}
        ],
        "education": [
            {{
                "degree": "Degree (e.g. B.S. Computer Science)",
                "institution": "University Name",
                "year": "Graduation Year (e.g. 2024)",
                "gpa": "GPA (optional)"
            }}
        ],
        "experience": [
            {{
                "role": "Job Title/Role",
                "company": "Company Name",
                "duration": "Start Date - End Date",
                "description": "Short description of responsibilities/achievements"
            }}
        ]
    }}
    
    Make sure to extract technical skills, libraries, frameworks, databases, and programming languages accurately.
    
    Resume Text:
    {resume_text}
    """
    
    response = generate_content_with_fallback(
        client=client,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    return parse_json_safely(response.text)

def generate_question(
    resume_json: Dict[str, Any], 
    question_type: str, 
    difficulty: str, 
    target_skill: Optional[str] = None, 
    history: List[Dict[str, str]] = [], 
    api_key: str = ""
) -> str:
    """Generates the next interview question based on resume, type, difficulty, and history."""
    client = get_client(api_key)
    
    history_str = ""
    if history:
        history_str = "\n".join([f"Q: {h['question']}\nA: {h.get('answer', '')}" for h in history])

    skills_str = ", ".join(resume_json.get("skills", []))
    projects_str = json.dumps(resume_json.get("projects", []))
    
    base_prompt = f"""
    You are an expert tech interviewer conducting a real-time job interview.
    Candidate Profile:
    - Name: {resume_json.get('name', 'Candidate')}
    - Skills: {skills_str}
    - Projects: {projects_str}
    
    Previous Interview Transcript:
    {history_str}
    
    Current Task: Generate the NEXT interview question.
    Question Type requested: {question_type}
    Difficulty requested: {difficulty}
    Target Skill (if Technical): {target_skill}
    
    Guidelines:
    1. If type is "INTRO", ask an icebreaker or general question about their background or projects (e.g., "Tell me about yourself" or "Tell me about your project X").
    2. If type is "TECHNICAL", ask a question focusing on "{target_skill}" at the "{difficulty}" level.
       - EASY: Basic concepts, definitions, syntax (e.g., list vs tuple).
       - MEDIUM: Code application, design, practical use-cases, debugging (e.g., decorators, how to optimize a query).
       - HARD: Deep internals, advanced architecture, scaling, complex problem-solving (e.g., metaclasses, event loops, concurrency bottlenecks).
    3. If type is "BEHAVIORAL", ask a situational question designed to evoke a STAR-formatted response (e.g., handling conflicts, adapting to change, solving a difficult bug under pressure).
    4. Keep the question natural, conversational, professional, and concise. Do NOT output anything other than the question text itself.
    """
    
    response = generate_content_with_fallback(
        client=client,
        contents=base_prompt
    )
    return response.text.strip()

def evaluate_answer(
    question: str, 
    answer: str, 
    question_type: str, 
    target_skill: Optional[str] = None, 
    api_key: str = ""
) -> Dict[str, Any]:
    """Evaluates an answer for technical, communication, and behavioral details."""
    client = get_client(api_key)
    
    prompt = f"""
    You are an expert technical recruiter. Evaluate the following candidate answer.
    
    Question: {question}
    Question Type: {question_type}
    Target Skill: {target_skill or "N/A"}
    Candidate Answer: {answer}
    
    Evaluate the response and output a JSON object with this EXACT structure:
    {{
        "technical_score": 0-100 (For INTRO questions, base this on how well they introduced their profile. For TECHNICAL, accuracy/depth. For BEHAVIORAL, depth of experience),
        "clarity": 0-100 (How structured and easy to follow is the response),
        "confidence": 0-100 (Assess from tone, phrasing, certainty, or completeness),
        "feedback": "Detailed constructive criticism on the content. Mention what they explained well and what they missed.",
        
        "grammar_score": 0-100 (Deduct points for grammatical errors, spelling mistakes, or poor phrasing),
        "vocabulary_score": 0-100 (Richness and appropriateness of industry-specific terms and general vocabulary),
        "fluency_score": 0-100 (Assess communication structure, presence of filler words like 'um', 'like', 'uh' or highly fragmented phrasing),
        "communication_feedback": "Constructive feedback on their communication style, grammar, and articulation.",
        
        "behavioral_star_score": 0-100 (Explicitly rate how well they utilized the STAR method: Situation, Task, Action, Result. For INTRO/TECHNICAL, give a default score of 70-80 depending on structure),
        "behavioral_star_feedback": "Detailed feedback on which STAR elements were missing or well-executed."
    }}
    
    Provide realistic, professional scoring. Be critical but constructive.
    """
    
    response = generate_content_with_fallback(
        client=client,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    return parse_json_safely(response.text)

def generate_report_summary(
    answers_evaluations: List[Dict[str, Any]], 
    skills: List[str],
    api_key: str = ""
) -> Dict[str, Any]:
    """Generates the strengths, weaknesses, and recommended topics based on all evaluations."""
    client = get_client(api_key)
    
    evals_summary = []
    for idx, ev in enumerate(answers_evaluations):
        evals_summary.append({
            "index": idx + 1,
            "question": ev.get("question"),
            "question_type": ev.get("question_type"),
            "target_skill": ev.get("target_skill"),
            "score": ev.get("technical_score"),
            "feedback": ev.get("feedback"),
            "comm_feedback": ev.get("communication_feedback")
        })
        
    prompt = f"""
    You are an expert interview panel summarizing a candidate's overall performance.
    
    Candidate Skills: {", ".join(skills)}
    
    Detailed Interview Evaluations:
    {json.dumps(evals_summary, indent=2)}
    
    Provide a final JSON summary matching this schema:
    {{
        "strengths": ["Strength 1 (specific to skills/concepts)", "Strength 2", ...],
        "weaknesses": ["Weakness 1 (specific gaps identified)", "Weakness 2", ...],
        "recommended_topics": ["Specific Topic to learn/study 1", "Topic 2", ...]
    }}
    
    Create a highly personalized evaluation based on their actual performance in the questions.
    """
    
    response = generate_content_with_fallback(
        client=client,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    return parse_json_safely(response.text)
