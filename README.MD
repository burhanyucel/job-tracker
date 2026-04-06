# Job Tracker System

AI-powered job application tracking system. Track your applications, analyze job postings with AI, and monitor your progress.

## 🚀 Live Demo
https://job-tracker-weil.onrender.com/

## 🛠 Tech Stack
- Python + FastAPI
- Google Gemini AI
- SQLite + SQLAlchemy
- JWT Authentication
- Tailwind CSS
- HTML/CSS/JavaScript

## ⚙️ Features
- User registration and login
- Add and track job applications
- AI analysis of job postings
- Status tracking (Applied, Interview, Offer, Rejected)
- Dashboard with statistics
- Each user sees only their own data

## 🔧 Setup
1. Clone the repo
2. `pip install -r requirements.txt`
3. Create `.env` file: `GEMINI_API_KEY=your_key` and `SECRET_KEY=your_secret`
4. `uvicorn main:app --reload`