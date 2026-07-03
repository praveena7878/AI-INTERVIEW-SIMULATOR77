import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

class Settings:
    PROJECT_NAME: str = "AI Interview Simulator API"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./interview_simulator.db")
    
    # Gemini API settings
    # The key can be set in the environment or passed from the frontend UI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

settings = Settings()
