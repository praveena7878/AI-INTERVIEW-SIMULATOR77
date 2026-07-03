from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from . import crud, schemas, llm, models
import json

# Define the structure of the interview flow
# Q0: Intro
# Q1: Technical - Skill 1
# Q2: Technical - Skill 2 (or Skill 1 if only 1 skill)
# Q3: Technical - Skill 3 (or alternate)
# Q4: Behavioral
# Q5: Behavioral
TOTAL_QUESTIONS = 6

def get_next_question_type_and_skill(
    current_index: int, 
    skills: List[str]
) -> tuple[str, Optional[str]]:
    """Determines the question type and target skill for the given question index."""
    if current_index == 0:
        return "INTRO", None
    elif current_index in [1, 2, 3]:
        # Technical questions: rotate through extracted skills
        if not skills:
            return "TECHNICAL", "General Programming"
        skill_idx = (current_index - 1) % len(skills)
        return "TECHNICAL", skills[skill_idx]
    else:
        # Behavioral questions
        return "BEHAVIORAL", None

def adjust_difficulty(
    current_difficulty: str, 
    last_score: float
) -> str:
    """Implements the Adaptive Difficulty logic based on the user's last answer score.
    
    Rules:
    - If score > 90: Medium -> Hard
    - If score > 80: Easy -> Medium
    - If score < 50: Hard -> Medium, Medium -> Easy
    """
    difficulty_map = ["EASY", "MEDIUM", "HARD"]
    try:
        curr_idx = difficulty_map.index(current_difficulty.upper())
    except ValueError:
        curr_idx = 0
        
    if last_score > 90:
        # Upgrade if possible
        if curr_idx < 2:
            return difficulty_map[curr_idx + 1]
    elif last_score > 80:
        # Upgrade Easy -> Medium
        if curr_idx == 0:
            return "MEDIUM"
    elif last_score < 50:
        # Downgrade if possible
        if curr_idx > 0:
            return difficulty_map[curr_idx - 1]
            
    return current_difficulty

def calculate_final_scores(
    answers: List[models.Answer]
) -> Dict[str, float]:
    """Calculates the weighted final score and category sub-scores.
    
    Formula:
    - Technical Skills = 50%
    - Communication = 20%
    - Confidence = 15%
    - Behavioral = 15%
    
    Sub-scores are aggregated across the relevant question types.
    """
    tech_scores = []
    comm_scores = []
    conf_scores = []
    beh_scores = []
    
    for ans in answers:
        # Communication is evaluated for all questions
        comm_avg = (ans.grammar_score + ans.vocabulary_score + ans.fluency_score) / 3.0
        comm_scores.append(comm_avg)
        conf_scores.append(ans.confidence)
        
        if ans.question_type == "TECHNICAL":
            tech_scores.append(ans.technical_score)
        elif ans.question_type == "BEHAVIORAL":
            beh_scores.append(ans.behavioral_star_score)
        elif ans.question_type == "INTRO":
            # Intro counts slightly towards behavioral and technical baseline
            tech_scores.append(ans.technical_score)
            beh_scores.append(ans.behavioral_star_score)
            
    avg_tech = sum(tech_scores) / len(tech_scores) if tech_scores else 70.0
    avg_comm = sum(comm_scores) / len(comm_scores) if comm_scores else 70.0
    avg_conf = sum(conf_scores) / len(conf_scores) if conf_scores else 70.0
    avg_beh = sum(beh_scores) / len(beh_scores) if beh_scores else 70.0
    
    overall_score = (
        (avg_tech * 0.50) + 
        (avg_comm * 0.20) + 
        (avg_conf * 0.15) + 
        (avg_beh * 0.15)
    )
    
    return {
        "overall_score": round(overall_score, 1),
        "technical_score": round(avg_tech, 1),
        "communication_score": round(avg_comm, 1),
        "confidence_score": round(avg_conf, 1),
        "behavioral_score": round(avg_beh, 1)
    }
