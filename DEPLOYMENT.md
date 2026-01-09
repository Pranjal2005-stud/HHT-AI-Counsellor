# Deployment Guide

## Frontend Deployment on Vercel

### 1. Prepare for Deployment
The frontend is now configured to use environment variables for the API URL.

### 2. Deploy to Vercel

1. **Connect to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Sign in with GitHub
   - Click "New Project"
   - Import your `HHT-AI-Counsellor` repository

2. **Configure Build Settings:**
   - Framework Preset: `Create React App`
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `build`

3. **Set Environment Variables:**
   - In Vercel dashboard, go to Project Settings > Environment Variables
   - Add: `REACT_APP_API_URL` = `https://your-backend-url.com`
   - Replace `your-backend-url.com` with your actual backend URL

### 3. Backend Deployment Options

#### Option A: Railway
1. Go to [railway.app](https://railway.app)
2. Connect GitHub repo
3. Deploy from root directory
4. Set environment variable: `GEMINI_API_KEY`

#### Option B: Render
1. Go to [render.com](https://render.com)
2. Create new Web Service
3. Connect GitHub repo
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Set environment variable: `GEMINI_API_KEY`

### 4. Update Frontend Environment Variable
Once backend is deployed, update the Vercel environment variable:
- `REACT_APP_API_URL` = `https://your-deployed-backend-url.com`

### 5. Redeploy Frontend
After updating the environment variable, trigger a new deployment in Vercel.

## Local Development
For local development, the app will automatically use `http://localhost:8000` as defined in `.env.local`.

## Environment Files
- `.env.example` - Template for environment variables
- `.env.local` - Local development (not committed to git)
- Vercel Environment Variables - Production settings