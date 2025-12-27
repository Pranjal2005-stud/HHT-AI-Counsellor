#  AI Tech Counsellor - Quick Start Guide

## Complete System Overview

Your AI Tech Counsellor is now a **full-stack application** with:

###  Backend Features
- **FastAPI** server with 8 tech domains
- **Gemini AI** integration for personalized recommendations
- **Smart caching** to minimize API calls
- **Fallback support** when Gemini is unavailable
- **Session management** with progress tracking

###  Frontend Features
- **React web interface** with modern UI
- **Real-time progress** tracking
- **Interactive assessment** flow
- **Responsive design** for all devices
- **Error handling** and loading states

###  AI Integration
- **Question rephrasing** at startup (1 batch call per domain)
- **Personalized explanations** for final recommendations (1 call per session)
- **Intelligent caching** to reduce API usage
- **Graceful fallbacks** when API is unavailable

##  Quick Setup (Windows)

### Option 1: Automated Setup
```bash
# Run the setup script
setup.bat

# Start both servers
start_servers.bat
```

### Option 2: Manual Setup
```bash
# 1. Backend setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 2. Environment setup
copy .env.example .env
# Edit .env and add: GEMINI_API_KEY=your_key_here

# 3. Frontend setup
cd frontend
npm install
cd ..

# 4. Start backend (Terminal 1)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 5. Start frontend (Terminal 2)
cd frontend
npm start
```

##  Access Points

- **Web Interface**: http://localhost:3000 ← **Start here!**
- **API Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

##  Testing Options

1. **Web Interface** (Recommended)
   - Open http://localhost:3000
   - Complete the interactive assessment

2. **API Testing**
   ```bash
   python test_api.py
   ```

3. **Manual API Testing**
   - Use the API docs at http://localhost:8000/docs

##  Gemini API Setup

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to `.env` file: `GEMINI_API_KEY=your_key_here`
4. Restart the backend server

**Note**: System works without Gemini API (uses fallback recommendations)

##  Assessment Flow

1. **Personal Info** → Name, location, education
2. **Domain Selection** → Choose from 8 tech domains
3. **Questions** → 10 domain-specific questions
4. **Results** → Skill level + AI-powered recommendations

##  Supported Domains

- Backend Development
- Frontend Development  
- Data Analytics
- Machine Learning
- DevOps
- Cybersecurity
- Data Engineering
- Data Structures & Algorithms

##  Troubleshooting

### Backend Issues
- Ensure Python 3.8+ is installed
- Check if port 8000 is available
- Verify all dependencies are installed

### Frontend Issues
- Ensure Node.js 16+ is installed
- Check if port 3000 is available
- Run `npm install` in frontend directory

### Gemini Issues
- Verify API key in `.env` file
- Check internet connection
- System works without Gemini (fallback mode)

##  Project Structure

```
AICOUNSELLOR/
├── Data/                    # Question JSON files
├── frontend/                # React web interface
├── state.py                 # Session management
├── engine.py                # Core logic + Gemini
├── gemini_service.py        # AI integration
├── main.py                  # FastAPI server
├── .env.example             # Environment template
├── setup.bat                # Automated setup
└── start_servers.bat        # Start both servers
```

##  Success Indicators

 Backend starts without errors
 Frontend loads at http://localhost:3000
 Can complete full assessment flow
 Receives personalized recommendations
 Gemini integration working (optional)

---

**Ready to assess your tech skills? Start at http://localhost:3000!** 