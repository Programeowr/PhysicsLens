# Quick Deploy: Vercel + Railway

The easiest deployment option with good free tiers.

## Step 1: Deploy Backend to Railway (5 minutes)

### Prerequisites
- GitHub account
- Your code pushed to GitHub

### Deploy Steps

1. **Go to [railway.app](https://railway.app)**

2. **Sign in with GitHub**

3. **Click "New Project"**

4. **Select "Deploy from GitHub repo"**

5. **Choose your PhysicsLens repository**

6. **Railway will auto-detect Python and deploy**
   - It reads `Procfile` automatically
   - Installs from `requirements.txt`
   - Starts with the command in `Procfile`

7. **Get your backend URL**
   - Click on your deployment
   - Go to "Settings" tab
   - Find "Domains" section
   - Copy the Railway-provided URL (e.g., `physicslens-api-production.up.railway.app`)
   - Or click "Generate Domain" if none exists

8. **Verify it works**
   - Open: `https://your-railway-url.railway.app/`
   - You should see: `{"detail":"Not Found"}` (this is normal, means API is running)

**Cost**: Free tier includes $5/month credit (should be enough for low traffic)

---

## Step 2: Deploy Frontend to Vercel (5 minutes)

### Prerequisites
- Backend URL from Step 1
- GitHub account

### Deploy Steps

1. **Go to [vercel.com](https://vercel.com)**

2. **Sign in with GitHub**

3. **Click "Add New..." → "Project"**

4. **Import your PhysicsLens repository**

5. **Configure the project:**
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `dist` (auto-detected)

6. **Add Environment Variable:**
   - Click "Environment Variables"
   - Key: `VITE_API_BASE`
   - Value: `https://your-railway-url.railway.app` (from Step 1)
   - Check all environments (Production, Preview, Development)
   - Click "Add"

7. **Click "Deploy"**
   - Wait 1-2 minutes for build
   - Vercel will give you a URL (e.g., `physicslens.vercel.app`)

8. **Test your deployment:**
   - Open your Vercel URL
   - Try the default physics problem
   - Click "Generate Diagram"
   - Should work end-to-end!

**Cost**: Free for hobby projects

---

## Step 3: Update CORS (Important!)

Your backend needs to allow requests from your frontend domain.

### Option A: Via Environment Variable (Recommended)

1. Go to Railway dashboard
2. Select your project
3. Go to "Variables" tab
4. Add new variable:
   - Key: `ALLOWED_ORIGINS`
   - Value: `https://your-vercel-url.vercel.app,https://www.your-custom-domain.com`
5. Redeploy (Railway auto-redeploys on variable changes)

### Option B: Update Code

Edit `physics_diagram/api.py`:

```python
import os

# Get allowed origins from environment or use defaults
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "https://physicslens.vercel.app"  # Replace with your actual URL
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit and push to trigger redeployment.

---

## Step 4: Custom Domain (Optional)

### For Frontend (Vercel)
1. Go to Project Settings → Domains
2. Add your domain
3. Update DNS records as instructed

### For Backend (Railway)
1. Go to Project → Settings → Domains
2. Click "Custom Domain"
3. Enter your domain (e.g., `api.yourdomain.com`)
4. Update DNS CNAME record

Then update `VITE_API_BASE` in Vercel to your custom backend domain.

---

## Troubleshooting

### Frontend shows "Unable to reach the API"
- Check `VITE_API_BASE` is set correctly in Vercel
- Make sure you included `https://` in the URL
- Redeploy frontend after changing environment variables

### Backend "CORS Error"
- Update `ALLOWED_ORIGINS` in Railway
- Make sure frontend URL matches exactly
- Check browser console for exact error

### Backend "Module not found"
- Check `requirements.txt` is complete
- Run: `pip freeze > requirements.txt` locally
- Push updated requirements.txt
- Railway will auto-redeploy

### Diagrams not generating
- Check Railway logs for errors
- Verify `/solve` endpoint works: `curl https://your-railway-url.railway.app/solve -X POST -H "Content-Type: application/json" -d '{"text":"test"}'`

---

## Testing Your Deployment

1. **Open your Vercel URL**

2. **Try these test cases:**

   ✅ **Simple case (should work instantly):**
   ```
   A 5kg block on a 30 degree incline
   ```

   ✅ **Missing fields case (should show alert):**
   ```
   A block slides down a ramp
   ```
   Should show: "Missing information. Please provide:" with list

   ✅ **Complex projectile:**
   ```
   A ball is thrown at 45 degrees with speed 20 m/s
   ```

3. **Check response times:**
   - Simple cases: < 1 second
   - LLM fallback: 10-15 seconds (if Ollama enabled)

---

## Monitoring

### Railway Logs
- Go to your Railway project
- Click on your service
- Click "Logs" tab
- See real-time backend logs

### Vercel Logs
- Go to your Vercel project
- Click "Deployments"
- Click on a deployment
- Click "Runtime Logs"

---

## Updating Your Deployment

### Update Backend
```bash
# Make changes to backend code
git add .
git commit -m "Update backend"
git push
# Railway auto-deploys on push to main/master
```

### Update Frontend
```bash
# Make changes to frontend code
git add .
git commit -m "Update frontend"
git push
# Vercel auto-deploys on push to main/master
```

---

## Cost Breakdown

### Free Tier Usage
- **Vercel**: 100 GB bandwidth/month, unlimited sites
- **Railway**: $5/month credit (~500 hours of small instance)
- **Total**: FREE for hobby projects

### If you exceed free tier
- **Vercel**: $20/month for Pro (rarely needed for small projects)
- **Railway**: Pay-as-you-go beyond $5 credit (~$0.000231/GB-s)

---

## Success Checklist

- [ ] Railway backend deployed and responding
- [ ] Railway URL obtained
- [ ] Vercel frontend deployed
- [ ] `VITE_API_BASE` environment variable set in Vercel
- [ ] CORS configured in Railway
- [ ] End-to-end test successful
- [ ] Missing fields alert displays correctly
- [ ] Response times acceptable

---

## What's Next?

1. **Add custom domain** (optional)
2. **Set up monitoring** (Sentry, LogRocket)
3. **Enable Ollama** for LLM fallback (requires separate server)
4. **Add analytics** (Google Analytics, Plausible)
5. **Set up CI/CD** (already automatic with Vercel + Railway)

Your PhysicsLens app is now live! 🚀

Share your deployment URL and let others use your physics diagram generator!
