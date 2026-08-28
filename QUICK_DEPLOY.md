# 🚀 Quick Deploy Guide

Get PhysicsLens live in **15 minutes** with these simple steps.

## 📋 Prerequisites

- [ ] GitHub account
- [ ] Your code pushed to GitHub
- [ ] Git installed locally

If you haven't pushed to GitHub yet:
```bash
# Initialize git if needed
git init
git add .
git commit -m "Initial commit"

# Create a new repo on GitHub, then:
git remote add origin https://github.com/yourusername/PhysicsLens.git
git branch -M main
git push -u origin main
```

---

## 🎯 Easiest Option: Railway + Vercel

**Total time**: ~15 minutes  
**Cost**: FREE (for hobby projects)  
**Difficulty**: ⭐ Beginner-friendly

### Part 1: Deploy Backend (Railway) - 5 mins

1. **Go to** → https://railway.app
2. **Click** "Login" → "Login with GitHub"
3. **Click** "New Project" → "Deploy from GitHub repo"
4. **Select** your PhysicsLens repository
5. **Wait** ~2 minutes for deployment
6. **Click** on your deployment → "Settings" → "Generate Domain"
7. **Copy** your Railway URL (e.g., `physicslens-api-production.up.railway.app`)

✅ Backend is live!

### Part 2: Deploy Frontend (Vercel) - 5 mins

1. **Go to** → https://vercel.com
2. **Click** "Sign Up" → "Continue with GitHub"
3. **Click** "Add New..." → "Project"
4. **Select** your PhysicsLens repository
5. **Configure**:
   - Framework: Vite (auto-detected)
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
6. **Add Environment Variable**:
   - Name: `VITE_API_BASE`
   - Value: `https://your-railway-url.railway.app` (paste from Part 1)
7. **Click** "Deploy"
8. **Wait** ~2 minutes for build
9. **Copy** your Vercel URL

✅ Frontend is live!

### Part 3: Configure CORS - 2 mins

1. **Go back to** Railway dashboard
2. **Click** your project → "Variables" tab
3. **Add variable**:
   - Key: `ALLOWED_ORIGINS`
   - Value: `https://your-vercel-url.vercel.app` (paste from Part 2)
4. **Save** (Railway auto-redeploys)

✅ Everything connected!

### Part 4: Test It! - 3 mins

1. **Open** your Vercel URL in a browser
2. **Try** the default physics problem
3. **Click** "Generate Diagram"
4. **See** the diagram appear!

🎉 **Congratulations!** Your app is live!

---

## 🔄 Alternative: Render + Netlify

**Time**: ~15 minutes  
**Cost**: FREE (but slower cold starts)

### Backend on Render

1. Go to https://render.com
2. Sign in with GitHub
3. "New +" → "Web Service"
4. Select PhysicsLens repo
5. Configure:
   - Name: `physicslens-api`
   - Environment: Python 3
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn physics_diagram.api:app --host 0.0.0.0 --port $PORT`
6. Click "Create Web Service"
7. Copy your Render URL

### Frontend on Netlify

1. Go to https://netlify.com
2. Sign in with GitHub
3. "Add new site" → "Import an existing project"
4. Select PhysicsLens repo
5. Configure:
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `frontend/dist`
6. Add environment variable:
   - Key: `VITE_API_BASE`
   - Value: Your Render URL
7. Click "Deploy"

---

## 🐳 Docker Option (Any VPS)

If you have a VPS (DigitalOcean, AWS, etc.):

```bash
# SSH into your server
ssh user@your-server.com

# Clone repo
git clone https://github.com/yourusername/PhysicsLens.git
cd PhysicsLens

# Build and run backend
docker build -t physicslens-api .
docker run -d -p 8000:8000 --name physicslens physicslens-api

# Build and serve frontend
cd frontend
npm install
npm run build
# Serve with nginx or any static file server
```

---

## 📊 What You Get

### Free Tier Limits

**Railway**:
- $5/month credit (FREE)
- ~500 hours of uptime
- Good for hobby projects

**Vercel**:
- 100 GB bandwidth/month
- Unlimited deployments
- Fast global CDN

**Perfect for**:
- Personal projects
- Portfolios
- Demos
- Low-traffic apps

### Performance

- **Backend response**: 50-500ms
- **Frontend load**: < 1 second
- **Diagram generation**: 50ms-15s (depending on complexity)

---

## 🛠️ Common Issues

### "Unable to reach API"
✅ Check `VITE_API_BASE` in Vercel settings
✅ Make sure URL includes `https://`
✅ Redeploy frontend after changing variables

### CORS Error
✅ Set `ALLOWED_ORIGINS` in Railway
✅ Include your exact Vercel URL
✅ Wait for Railway to redeploy

### Build Failed
✅ Check `requirements.txt` is up-to-date
✅ Run `pip freeze > requirements.txt` locally
✅ Push changes to GitHub

---

## 🎨 Customization

### Add Your Own Domain

**For Backend** (Railway):
1. Settings → Domains → "Custom Domain"
2. Add `api.yourdomain.com`
3. Update CNAME in your DNS

**For Frontend** (Vercel):
1. Settings → Domains → "Add"
2. Follow DNS instructions
3. Update `VITE_API_BASE` to your custom API domain

### Update Your App

Just push to GitHub:
```bash
git add .
git commit -m "Update app"
git push
```
Both platforms auto-deploy! 🎉

---

## 📈 Next Steps

- [ ] Add custom domain
- [ ] Set up monitoring (optional)
- [ ] Enable LLM fallback (requires Ollama hosting)
- [ ] Add analytics
- [ ] Share with friends!

---

## 💡 Pro Tips

1. **Auto-deployment**: Both platforms deploy automatically on git push
2. **Preview deployments**: Vercel creates preview URLs for each PR
3. **Logs**: Check Railway/Vercel dashboards for debugging
4. **Environment variables**: Can be changed without code changes
5. **Free tier**: Should be enough for 100-1000 users/month

---

## 📞 Need Help?

- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com

---

## ✨ You're Done!

Your PhysicsLens app is now:
- ✅ Live on the internet
- ✅ Automatically deployed on git push
- ✅ Hosted on reliable platforms
- ✅ Using the hybrid parser with LLM fallback
- ✅ Showing beautiful missing field alerts

**Share your URL and let others generate physics diagrams!** 🎉

Example deployment URLs:
- Frontend: https://physicslens.vercel.app
- Backend: https://physicslens-api-production.up.railway.app
