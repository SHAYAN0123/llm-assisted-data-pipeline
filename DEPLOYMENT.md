# Deployment Guide

This project has two parts:
1. **Frontend**: Static HTML/CSS/JS hosted on GitHub Pages
2. **Backend**: Flask API that needs to be deployed separately

## Frontend Deployment (GitHub Pages)

Your frontend is already deployed at: `https://SHAYAN0123.github.io/llm-assisted-data-pipeline/`

## Backend Deployment

The Flask backend needs to be deployed to a server. Choose one option:

### Option 1: Railway (Recommended - Easiest)

1. **Sign up** at https://railway.app (free tier available)
2. **Connect GitHub**:
   - Go to Dashboard → New Project → GitHub Repo
   - Select `llm-assisted-data-pipeline`
3. **Railway auto-detects Python** and deploys automatically
4. **Get your backend URL**: Dashboard → Deployments → Copy the URL
5. **Update frontend**: In `docs/index.html`, replace `window.location.origin` with your Railway URL:

```javascript
const apiBaseUrl = 'https://your-railway-app.railway.app';
```

### Option 2: Render (Also Free)

1. **Sign up** at https://render.com (free tier)
2. **Create Web Service**:
   - GitHub → Connect repo → Select this repo
   - Name: `llm-data-pipeline`
   - Runtime: Python 3.10
   - Build command: `pip install -r requirements-deploy.txt`
   - Start command: `python app.py`
3. **Get your URL** from Render dashboard
4. **Update frontend** with your Render URL

### Option 3: Heroku (Paid, but easy)

```bash
# Install Heroku CLI
brew tap heroku/brew && brew install heroku

# Login
heroku login

# Create app
heroku create my-data-pipeline

# Deploy
git push heroku main

# Get URL
heroku open
```

## Updating Frontend with Backend URL

Once you have your backend deployed, update `docs/index.html`:

Find these lines (around line 700):
```javascript
const apiBaseUrl = window.location.hostname === 'localhost' 
    ? 'http://localhost:3000' 
    : window.location.origin;
```

Replace with your actual backend URL:
```javascript
const apiBaseUrl = 'https://your-backend-url.railway.app';
```

Then commit and push:
```bash
git add docs/index.html
git commit -m "update: point frontend to deployed backend"
git push
```

## Local Testing

For local development:
```bash
# Terminal 1: Start backend on port 3000
PORT=3000 python app.py

# Terminal 2: Visit http://localhost:3000
# The frontend and backend are served from the same port
```

## Troubleshooting

**Error: "Unexpected token '<'"**
- This means frontend is getting HTML instead of JSON
- The backend URL is wrong or backend isn't running
- Check your deployed backend URL in browser: `https://your-url.railway.app/api/health`

**CORS errors**
- Flask has CORS enabled, should work from anywhere
- Check Network tab in browser DevTools (F12)

**Backend works locally but not deployed**
- Check deployment logs: Railway → Logs or Render → Logs
- Ensure all dependencies in `requirements-deploy.txt`
- Check that Flask is listening on `0.0.0.0` (it is by default)

## Next Steps

1. Deploy backend to Railway/Render (5 minutes)
2. Get the backend URL
3. Update frontend `docs/index.html` with backend URL
4. Commit and push to GitHub
5. Test at your GitHub Pages URL
