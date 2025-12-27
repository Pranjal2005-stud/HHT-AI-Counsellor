# HHT AI Counsellor

An intelligent conversational system that assesses users' technical skills and provides personalized learning recommendations through a ChatGPT-like interface.

## Features

- **Conversational Interface**: ChatGPT-like chat experience for natural interaction
- **Multi-domain Assessment**: Supports 8 tech domains (Backend, Frontend, Data Analytics, ML, DevOps, Cybersecurity, Data Engineering, DSA)
- **Intelligent Response Classification**: Handles yes/no answers, confused responses, and off-topic questions
- **Detailed Assessment Results**: Shows areas to improve with explanations for missed questions
- **AI-Powered Recommendations**: Uses Gemini AI for personalized explanations and suggestions
- **Post-Assessment Chat**: Continue conversations after assessment completion
- **Modern UI**: Blue/yellow theme with full-screen responsive design

## Tech Stack

**Backend:**
- FastAPI (Python)
- Google Gemini AI API
- Pydantic for data validation
- CORS middleware for frontend integration

**Frontend:**
- React.js
- Axios for API calls
- Modern CSS with blue/yellow theme
- Responsive design

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- Google Gemini API key (optional but recommended)

### Backend Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd AICOUNSELLOR
```

2. **Create virtual environment**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
```bash
# Create .env file
echo "GEMINI_API_KEY=your_actual_api_key_here" > .env
```

5. **Start backend server**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm start
```

### Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Usage

1. **Start Conversation**: Enter your name when prompted
2. **Provide Education**: Share your educational background
3. **Select Domain**: Choose from 8 technical domains
4. **Assessment**: Answer 6 yes/no questions about your experience
5. **Results**: View detailed results with improvement suggestions
6. **Chat**: Ask questions about your results and get personalized advice

## Assessment Features

### Response Classification
- **YES responses**: "yes", "definitely", "sure" → Adds score, moves to next question
- **NO responses**: "no", "never", "not really" → Provides explanation, moves to next question
- **Invalid responses**: Prompts for yes/no answer

### Detailed Results
- **Skill Level**: Beginner (0-49%), Intermediate (50-79%), Advanced (80%+)
- **Areas to Improve**: Shows questions answered "No" with explanations
- **Personalized Recommendations**: Domain-specific topics and projects
- **Post-Assessment Chat**: Ask for improvement tips and guidance

## Supported Domains

1. **Backend Development**: APIs, databases, authentication, cloud services
2. **Frontend Development**: React/Vue/Angular, responsive design, performance
3. **Data Analytics**: SQL, visualization, statistical analysis
4. **Machine Learning**: Algorithms, model evaluation, deployment
5. **DevOps**: Docker, Kubernetes, CI/CD, cloud platforms
6. **Cybersecurity**: Penetration testing, compliance, security architecture
7. **Data Engineering**: ETL pipelines, big data tools, streaming
8. **Algorithms & Data Structures**: Coding interviews, competitive programming

## API Endpoints

- `POST /start` - Start new conversation session
- `POST /personal-info` - Submit personal information
- `POST /answer` - Submit assessment answers
- `POST /chat` - Post-assessment chat
- `GET /domains` - Get available domains

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini AI for intelligent responses
- FastAPI for the robust backend framework
- React for the modern frontend interface