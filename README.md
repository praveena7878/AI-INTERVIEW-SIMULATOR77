# AI Interview Simulator (Intervue.ai)

Intervue.ai is an agentic coding solution that simulates professional, multi-stage job interviews. By analyzing an uploaded PDF resume, it automatically extracts core skills, generates custom introductory, technical, and behavioral questions, dynamically adjusts interview difficulty based on performance, evaluates candidate communication, and compiles a comprehensive feedback dashboard.

---

## Technical Stack & Features

- **Frontend**: React.js, Vite, Custom CSS (Dark Theme, glassmorphism, responsive grids), and Recharts for progress trends.
- **Voice Integration**: Native browser Web Speech API (Speech Recognition for speech-to-text dictation and Speech Synthesis for text-to-speech reading).
- **Backend**: FastAPI (Python), SQLite (out-of-the-box local database), and SQLAlchemy ORM.
- **AI Engine**: Gemini API (`gemini-1.5-flash`) for parsing resumes, question generation, answer evaluation, behavioral checks, and communication analysis.

---

## Setup & Running Instructions

Follow these steps to run the application locally on Windows.

### Prerequisites
1. **Python 3.10 or higher** installed.
2. **Node.js 18 or higher** installed.
3. **Gemini API Key** (Get one from [Google AI Studio](https://aistudio.google.com)).

---

### Step 1: Start the Backend Server

1. Open PowerShell or Command Prompt.
2. Navigate to the backend directory:
   ```cmd
   cd backend
   ```
3. Create a Python virtual environment:
   ```cmd
   python -m venv venv
   ```
4. Activate the virtual environment:
   - On Windows (Command Prompt):
     ```cmd
     venv\Scripts\activate
     ```
   - On Windows (PowerShell):
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
5. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```
6. Start the server using Uvicorn:
   ```cmd
   uvicorn app.main:app --reload --port 8000
   ```
   The backend API will run at `http://localhost:8000`.

---

### Step 2: Start the Frontend React App

1. Open a new terminal window.
2. Navigate to the frontend directory:
   ```cmd
   cd frontend
   ```
3. Install node dependencies:
   ```cmd
   npm install
   ```
4. Run the Vite development server:
   ```cmd
   npm run dev
   ```
5. Open your browser and navigate to `http://localhost:3000`.

---

### Step 3: Run Unit Tests

To verify that the adaptive difficulty and scoring logic work correctly, you can run the test suite:
1. Open a terminal in the `backend` directory with the virtual environment active.
2. Run:
   ```cmd
   python -m unittest tests/test_flow.py
   ```

---

## How It Works

1. **Resume Analysis**: When you upload a PDF resume, `pdfplumber` extracts raw text and passes it to Gemini. Gemini identifies skills (e.g. Python, SQL), projects, education, and experience, creating a structured candidate profile.
2. **Dynamic Questioning**: The simulator starts with an introductory question ("Tell me about yourself"). It then shifts to technical questions targeting the extracted skills, and wraps up with behavioral scenarios (requesting STAR-method responses).
3. **Adaptive Difficulty**:
   - Technical questions start at the selected level (default: **EASY**).
   - If you score **> 80%** or **> 90%** on an answer, difficulty shifts up (**Easy → Medium → Hard**).
   - If you score **< 50%**, difficulty shifts down (**Hard → Medium → Easy**) to guide you through a comfortable learning path.
4. **Scoring Breakdown**:
   - **Technical Content**: 50%
   - **Communication Style**: 20% (Grammar, Vocabulary, Fluency)
   - **Confidence Level**: 15%
   - **Behavioral Structure**: 15% (STAR Method)
5. **Interactive Dashboard**: View previous sessions, trace performance trends over multiple attempts, and review detail feedback for every single question answered.
