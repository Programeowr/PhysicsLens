# PhysicsLens Deployment Guide

Complete guide to hosting PhysicsLens frontend and backend in production.

## Table of Contents
1. [Quick Start (Free Options)](#quick-start-free-options)
2. [Architecture Overview](#architecture-overview)
3. [Frontend Deployment](#frontend-deployment)
4. [Backend Deployment](#backend-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Production Considerations](#production-considerations)

---

## Quick Start (Free Options)

### Option 1: Vercel (Frontend) + Railway (Backend)
**Best for**: Quick deployment, free tier available
**Time**: ~15 minutes

### Option 2: Netlify (Frontend) + Render (Backend)
**Best for**: Simplicity, good free tier
**Time**: ~15 minutes

### Option 3: GitHub Pages (Frontend) + Fly.io (Backend)
**Best for**: Static hosting + container deployment
**Time**: ~20 minutes

---

## Architecture Overview

```
┌─────────────┐         HTTPS          ┌─────────────┐
│   Browser   │ ──────────────────────▶│  Frontend   │
│             │                        │   (Vite)    │
└─────────────┘                        └─────────────┘
                                              │
                                              │ API Calls
                                              ▼
                                       ┌─────────────┐
                                       │   Backend   │
                                       │  (FastAPI)  │
                                       └─────────────┘
                                              │
                                              │ Optional
                                              ▼
                                       ┌─────────────┐
                                       │   Ollama    │
                                       │ (qwen2.5:7b)│
                                       └─────────────┘
```

---

## Frontend Deployment

### Prerequisites
```bash
cd frontend
npm install
npm run build
# Creates a 'dist' folder with static files
```

### Option A: Vercel (Recommended)

**Setup:**
1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Deploy:
   ```bash
   cd frontend
   vercel
   ```

3. Follow prompts:
   - Login to Vercel
   - Link to project (or create new)
   - Accept defaults

4. Set environment variable in Vercel dashboard:
   - Go to Project Settings → Environment Variables
   - Add: `VITE_API_BASE` = `https://your-backend-url.com`
   - Redeploy

**Vercel Configuration** (`frontend/vercel.json`):
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

### Option B: Netlify

**Setup:**
1. Install Netlify CLI:
   ```bash
   npm install -g netlify-cli
   ```

2. Deploy:
   ```bash
   cd frontend
   netlify deploy --prod
   ```

3. Set build directory to `dist`

4. Add environment variable:
   - Site Settings → Build & Deploy → Environment
   - Add: `VITE_API_BASE` = `https://your-backend-url.com`

**Netlify Configuration** (`frontend/netlify.toml`):
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### Option C: GitHub Pages

**Setup:**
1. Update `frontend/vite.config.js`:
   ```javascript
   export default defineConfig({
     base: '/PhysicsLens/',  // Replace with your repo name
     // ... rest of config
   })
   ```

2. Build and deploy:
   ```bash
   cd frontend
   npm run build
   npm install -g gh-pages
   gh-pages -d dist
   ```

3. Enable GitHub Pages in repo settings

---

## Backend Deployment

### Prerequisites

Create required files first:

#### 1. `requirements.txt` (if not exists)
```bash
cd c:\Users\V Sai Akhil\Projects\PhysicsLens
.venv314\Scripts\python.exe -m pip freeze > requirements.txt
```

#### 2. Create `Procfile` for most platforms

#### 3. Create `Dockerfile` for container platforms

### Option A: Railway (Recommended for Python)

**Setup:**
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your PhysicsLens repository
5. Railway auto-detects Python

**Configuration:**
- **Start Command**: `uvicorn physics_diagram.api:app --host 0.0.0.0 --port $PORT`
- **Root Directory**: `/` (leave as project root)

**Environment Variables** (in Railway dashboard):
- `PORT`: (automatically set by Railway)
- `PYTHON_VERSION`: `3.14` (optional, to match your local version)

**Cost**: Free tier includes $5/month credit

### Option B: Render

**Setup:**
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repo
5. Configure:
   - **Name**: physicslens-api
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn physics_diagram.api:app --host 0.0.0.0 --port $PORT`

**Environment Variables**:
- Add any needed variables in dashboard

**Cost**: Free tier available (spins down after inactivity)

### Option C: Fly.io

**Setup:**
1. Install Fly CLI:
   ```bash
   # Windows
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. Login:
   ```bash
   fly auth login
   ```

3. Initialize app:
   ```bash
   fly launch --no-deploy
   ```

4. Deploy:
   ```bash
   fly deploy
   ```

**Cost**: Free tier includes 3 VMs

### Option D: Heroku

**Setup:**
1. Install Heroku CLI
2. Login:
   ```bash
   heroku login
   ```

3. Create app:
   ```bash
   heroku create physicslens-api
   ```

4. Deploy:
   ```bash
   git push heroku main
   ```

**Procfile**:
```
web: uvicorn physics_diagram.api:app --host 0.0.0.0 --port $PORT
```

**Cost**: Free tier discontinued, starts at $5/month

---

## Required Configuration Files

Let me create these files for you:

### 1. Dockerfile (for containerized deployments)

### 2. .dockerignore

### 3. Procfile (for Heroku/Railway)

### 4. railway.json (for Railway)

### 5. render.yaml (for Render)

---

## Environment Configuration

### Production Environment Variables

**Frontend** (`.env.production`):
```env
VITE_API_BASE=https://your-backend-url.com
```

**Backend** (set in hosting dashboard):
```env
# Railway/Render/Fly.io set PORT automatically
PORT=8000

# Optional: if you want to use LLM fallback in production
OLLAMA_HOST=http://your-ollama-instance:11434

# CORS origins (comma-separated)
ALLOWED_ORIGINS=https://your-frontend-url.com,https://www.your-domain.com
```

---

## Production Considerations

### 1. CORS Configuration

Update `physics_diagram/api.py` for production:
```python
import os

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Replace "*" with your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. LLM Fallback in Production

**Option 1: Disable LLM** (deterministic only)
- Faster, cheaper
- 68.2% accuracy
- Set default parser to "deterministic" in code

**Option 2: Host Ollama Separately**
- Better accuracy (89.4%)
- Requires additional server for Ollama
- Options:
  - Separate VPS (DigitalOcean, Linode)
  - Modal.com (GPU hosting)
  - Replicate.com (pay-per-use)

**Option 3: Replace with API-based LLM**
- OpenAI GPT-4
- Anthropic Claude
- Google Gemini
- Modify `llm_parser.py` to use API instead of Ollama

### 3. Performance Optimization

**Backend**:
- Use gunicorn with multiple workers:
  ```bash
  gunicorn physics_diagram.api:app -w 4 -k uvicorn.workers.UvicornWorker
  ```

**Frontend**:
- Already optimized with Vite build
- Compression enabled
- Code splitting automatic

### 4. Monitoring & Logging

Add to backend:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

Consider adding:
- Sentry for error tracking
- LogRocket for session replay
- Google Analytics for usage

### 5. Security

- [ ] Set proper CORS origins (not "*")
- [ ] Add rate limiting
- [ ] Use HTTPS everywhere
- [ ] Set secure headers
- [ ] Validate input sizes
- [ ] Add API authentication (if needed)

---

## Deployment Checklist

### Pre-deployment
- [ ] Frontend builds successfully (`npm run build`)
- [ ] Backend runs with gunicorn
- [ ] All environment variables identified
- [ ] CORS origins configured
- [ ] Error handling tested

### Frontend Deployment
- [ ] Choose hosting platform (Vercel/Netlify/Pages)
- [ ] Deploy frontend
- [ ] Set `VITE_API_BASE` environment variable
- [ ] Verify frontend loads
- [ ] Test on mobile

### Backend Deployment
- [ ] Choose hosting platform (Railway/Render/Fly.io)
- [ ] Create `requirements.txt`
- [ ] Configure start command
- [ ] Deploy backend
- [ ] Verify `/solve` endpoint works
- [ ] Test with actual requests

### Final Testing
- [ ] Test complete flow end-to-end
- [ ] Test error cases (missing fields)
- [ ] Test different scenarios (incline, projectile, etc.)
- [ ] Check response times
- [ ] Verify CORS working
- [ ] Test on different devices

---

## Cost Estimate

### Free Tier (Hobby Projects)
- **Frontend**: Vercel or Netlify (Free forever)
- **Backend**: Railway ($5/month credit, free tier) or Render (free, sleeps after inactivity)
- **Total**: $0-5/month

### Low Traffic (< 10k requests/month)
- **Frontend**: Vercel or Netlify (Free)
- **Backend**: Railway or Render ($5-7/month)
- **Total**: $5-7/month

### Medium Traffic (< 100k requests/month)
- **Frontend**: Vercel Pro ($20/month)
- **Backend**: Railway or Fly.io ($10-20/month)
- **Ollama** (optional): DigitalOcean Droplet ($24/month for GPU)
- **Total**: $30-64/month

---

## Quick Deploy Commands

I'll create scripts to automate deployment for each platform.

Which platform would you like to use?
1. **Railway (backend) + Vercel (frontend)** - Easiest, good free tier
2. **Render (backend) + Netlify (frontend)** - Simple, reliable
3. **Fly.io (backend) + GitHub Pages (frontend)** - More control
4. **Custom VPS** - Full control, more setup required

Let me know and I'll create the specific deployment files and scripts!
