import os
import sys
import unittest
from datetime import datetime

# Adjust Python path to load backend app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import models, interview, schemas

class TestInterviewFlow(unittest.TestCase):
    def test_difficulty_adaptation(self):
        """Tests the adaptive difficulty rules."""
        # Rules:
        # - If last score > 90: upgrade (EASY -> MEDIUM, MEDIUM -> HARD)
        # - If last score > 80: upgrade (EASY -> MEDIUM)
        # - If last score < 50: downgrade (HARD -> MEDIUM, MEDIUM -> EASY)
        
        # Test upgrades
        self.assertEqual(interview.adjust_difficulty("EASY", 95.0), "MEDIUM")
        self.assertEqual(interview.adjust_difficulty("EASY", 85.0), "MEDIUM")
        self.assertEqual(interview.adjust_difficulty("EASY", 75.0), "EASY")  # No change
        self.assertEqual(interview.adjust_difficulty("MEDIUM", 95.0), "HARD")
        self.assertEqual(interview.adjust_difficulty("MEDIUM", 85.0), "MEDIUM") # No change (needs > 90 to go HARD)
        self.assertEqual(interview.adjust_difficulty("HARD", 98.0), "HARD")     # Max difficulty
        
        # Test downgrades
        self.assertEqual(interview.adjust_difficulty("HARD", 45.0), "MEDIUM")
        self.assertEqual(interview.adjust_difficulty("MEDIUM", 40.0), "EASY")
        self.assertEqual(interview.adjust_difficulty("EASY", 30.0), "EASY")      # Min difficulty
        
    def test_scoring_weights(self):
        """Tests final score calculation formula.
        
        Weights:
        - Technical: 50%
        - Communication: 20%
        - Confidence: 15%
        - Behavioral: 15%
        """
        # Mock answers
        a1 = models.Answer(
            question_type="INTRO",
            technical_score=80.0,
            grammar_score=80.0,
            vocabulary_score=80.0,
            fluency_score=80.0,
            confidence=80.0,
            behavioral_star_score=80.0
        )
        
        a2 = models.Answer(
            question_type="TECHNICAL",
            technical_score=90.0,
            grammar_score=70.0,
            vocabulary_score=75.0,
            fluency_score=80.0, # Avg comm = 75
            confidence=85.0,
            behavioral_star_score=0.0 # Not behavioral, shouldn't affect
        )
        
        a3 = models.Answer(
            question_type="BEHAVIORAL",
            technical_score=0.0, # Not technical, shouldn't affect
            grammar_score=80.0,
            vocabulary_score=80.0,
            fluency_score=80.0, # Avg comm = 80
            confidence=75.0,
            behavioral_star_score=85.0
        )
        
        answers = [a1, a2, a3]
        scores = interview.calculate_final_scores(answers)
        
        # Check overall aggregation
        # Expected Technical: Avg of (a1.tech, a2.tech) = (80 + 90) / 2 = 85%
        self.assertEqual(scores["technical_score"], 85.0)
        
        # Expected Comm: Avg of (a1.comm=80, a2.comm=75, a3.comm=80) = 78.33%
        # Expected Conf: Avg of (80, 85, 75) = 80.0%
        # Expected Behavioral: Avg of (a1.beh=80, a3.beh=85) = 82.5%
        # Overall = (85 * 0.5) + (78.33 * 0.2) + (80.0 * 0.15) + (82.5 * 0.15)
        #         = 42.5 + 15.666 + 12.0 + 12.375
        #         = 82.54% -> rounded to 82.5%
        self.assertAlmostEqual(scores["overall_score"], 82.5, places=1)

if __name__ == "__main__":
    unittest.main()
