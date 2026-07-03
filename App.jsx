import React, { useState, useEffect } from 'react'
import { Key, User, FileText, LayoutDashboard, HelpCircle, LogOut } from 'lucide-react'
import Dashboard from './components/Dashboard'
import ResumeUpload from './components/ResumeUpload'
import InterviewRoom from './components/InterviewRoom'
import Report from './components/Report'

function App() {
  const [userName, setUserName] = useState('')
  const [user, setUser] = useState(null) // { id, name, skills, resume_json }
  const [apiKey, setApiKey] = useState('')
  const [activeScreen, setActiveScreen] = useState('welcome') // welcome, dashboard, upload, interview, report
  const [activeInterviewId, setActiveInterviewId] = useState(null)
  const [activeReportId, setActiveReportId] = useState(null)
  
  // App initialization: load API key and profile from localStorage if exists
  useEffect(() => {
    const savedKey = localStorage.getItem('gemini_api_key')
    if (savedKey) setApiKey(savedKey)
    
    const savedUser = localStorage.getItem('user_profile')
    if (savedUser) {
      const parsed = JSON.parse(savedUser)
      setUser(parsed)
      // Check if they already have skills extracted to decide where to route
      if (parsed.skills && parsed.skills.length > 0) {
        setActiveScreen('dashboard')
      } else {
        setActiveScreen('upload')
      }
    }
  }, [])

  const handleRegister = async (e) => {
    e.preventDefault()
    if (!userName.trim()) return

    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: userName }),
      })

      if (response.ok) {
        const data = await response.json()
        setUser(data)
        localStorage.setItem('user_profile', JSON.stringify(data))
        if (data.skills && data.skills.length > 0) {
          setActiveScreen('dashboard')
        } else {
          setActiveScreen('upload')
        }
      } else {
        alert('Failed to register. Please make sure the backend is running.')
      }
    } catch (error) {
      console.error('Registration error:', error)
      alert('Could not connect to the backend server. Please verify it is running on http://localhost:8000.')
    }
  }

  const handleSaveKey = (e) => {
    e.preventDefault()
    localStorage.setItem('gemini_api_key', apiKey)
    alert('Gemini API key saved locally in browser storage.')
  }

  const handleLogout = () => {
    localStorage.removeItem('user_profile')
    setUser(null)
    setUserName('')
    setActiveScreen('welcome')
  }

  const handleStartInterview = async (difficulty = 'EASY') => {
    if (!apiKey) {
      alert('Please configure your Gemini API Key in the top panel before starting!')
      return
    }

    try {
      const response = await fetch('/api/start-interview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Gemini-API-Key': apiKey
        },
        body: JSON.stringify({
          user_id: user.id,
          difficulty: difficulty
        })
      })

      if (response.ok) {
        const data = await response.json()
        setActiveInterviewId(data.interview_id)
        setActiveScreen('interview')
      } else {
        const errData = await response.json()
        alert(`Error starting interview: ${errData.detail || 'Internal error'}`)
      }
    } catch (error) {
      console.error('Start interview error:', error)
      alert('Connection error starting interview.')
    }
  }

  const viewReport = (interviewId) => {
    setActiveReportId(interviewId)
    setActiveScreen('report')
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header Bar */}
      <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => user && setActiveScreen('dashboard')}>
          <div className="bg-gradient-to-tr from-indigo-500 to-violet-600 p-2 rounded-xl text-white font-bold text-lg shadow-lg shadow-indigo-500/20">
            🎙️
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent m-0">
              Intervue.ai
            </h1>
            <p className="text-[10px] text-zinc-500 font-medium m-0 tracking-wider uppercase">AI INTERVIEW SIMULATOR</p>
          </div>
        </div>

        {user && (
          <div className="flex items-center gap-6">
            {/* API Key Form */}
            <form onSubmit={handleSaveKey} className="flex items-center gap-2 bg-zinc-900/60 border border-zinc-800 p-1.5 rounded-lg">
              <Key className="w-4 h-4 text-zinc-500 ml-2" />
              <input
                type="password"
                placeholder="Enter Gemini API Key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                autoComplete="new-password"
                className="bg-transparent text-sm border-none outline-none text-zinc-300 w-44 focus:w-64 transition-all duration-300"
              />
              <button type="submit" className="text-xs font-semibold bg-zinc-800 hover:bg-zinc-700 px-3 py-1.5 rounded-md transition-colors">
                Save
              </button>
            </form>

            <nav className="flex items-center gap-1 bg-zinc-900/40 p-1 rounded-lg border border-zinc-800/40">
              <button
                onClick={() => setActiveScreen('dashboard')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  activeScreen === 'dashboard' ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20' : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </button>
              <button
                onClick={() => setActiveScreen('upload')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  activeScreen === 'upload' ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20' : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                <FileText className="w-4 h-4" />
                Resume
              </button>
            </nav>

            <div className="flex items-center gap-3 pl-4 border-l border-zinc-800">
              <div className="flex flex-col text-right">
                <span className="text-sm font-semibold text-white">{user.name}</span>
                <span className="text-[10px] text-zinc-500">Candidate</span>
              </div>
              <button
                onClick={handleLogout}
                title="Logout"
                className="p-2 rounded-lg hover:bg-zinc-900 text-zinc-400 hover:text-zinc-200 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </header>

      {/* Main Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8 flex flex-col justify-center">
        {activeScreen === 'welcome' && (
          <div className="max-w-md w-full mx-auto glass-card p-8 text-center border-zinc-800/80">
            <span className="text-4xl">🤖</span>
            <h2 className="text-2xl font-extrabold mt-4 mb-2">Welcome to Intervue.ai</h2>
            <p className="text-zinc-400 text-sm mb-6">
              An intelligent, adaptive simulator that conducts full-length interviews based on your resume skills, evaluates your answers, and scores your communication.
            </p>

            <form onSubmit={handleRegister} className="flex flex-col gap-4 text-left">
              <div>
                <label className="form-label">Candidate Name</label>
                <input
                  type="text"
                  required
                  placeholder="Enter your name"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  className="form-input w-full"
                />
              </div>
              
              <div>
                <label className="form-label">Gemini API Key (Required for AI features)</label>
                <div className="relative flex items-center">
                  <input
                    type="password"
                    placeholder="AI-xxxxxx"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    autoComplete="new-password"
                    className="form-input w-full pr-10"
                  />
                  <Key className="w-4 h-4 text-zinc-500 absolute right-3" />
                </div>
                <p className="text-[10px] text-zinc-500 mt-2">
                  Used directly in your browser. Not stored on any external servers. Get one from Google AI Studio.
                </p>
              </div>

              <button type="submit" className="btn-primary w-full justify-center mt-2">
                Get Started
              </button>
            </form>
          </div>
        )}

        {activeScreen === 'upload' && user && (
          <ResumeUpload 
            user={user} 
            setUser={setUser} 
            apiKey={apiKey} 
            onUploadSuccess={() => setActiveScreen('dashboard')} 
          />
        )}

        {activeScreen === 'dashboard' && user && (
          <Dashboard 
            user={user} 
            onStartInterview={handleStartInterview} 
            onViewReport={viewReport} 
          />
        )}

        {activeScreen === 'interview' && activeInterviewId && (
          <InterviewRoom 
            interviewId={activeInterviewId} 
            apiKey={apiKey}
            onComplete={(reportId) => {
              setActiveReportId(reportId);
              setActiveScreen('report');
            }}
            onExit={() => setActiveScreen('dashboard')}
          />
        )}

        {activeScreen === 'report' && activeReportId && (
          <Report 
            interviewId={activeReportId} 
            apiKey={apiKey} 
            onBack={() => setActiveScreen('dashboard')} 
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-900 bg-zinc-950 py-4 text-center text-xs text-zinc-500">
        &copy; {new Date().getFullYear()} Intervue.ai. Powered by Gemini Flash 1.5. Built for professional interview success.
      </footer>
    </div>
  )
}

export default App
