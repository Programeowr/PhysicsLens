# 📋 Deployment Checklist

Use this checklist to ensure smooth deployment.

## ✅ Pre-Deployment (Local)

### Code Preparation
- [ ] All changes committed to git
- [ ] Code pushed to GitHub
- [ ] `requirements.txt` is up-to-date
- [ ] Frontend builds successfully: `npm --prefix frontend run build`
- [ ] Backend runs locally: Test `/solve` endpoint
- [ ] Tests passing (if you have them)

### Files Created
- [x] `Dockerfile` - For container deployment
- [x] `.dockerignore` - Exclude unnecessary files
- [x] `Procfile` - For Heroku/Railway
- [x] `railway-config.json` - Railway configuration
- [x] `render.yaml` - Render configuration
- [x] `frontend/netlify.toml` - Netlify configuration
- [x] `frontend/vercel.json` - Vercel configuration

### Code Updates
- [x] API CORS configured with environment variable
- [x] Frontend `.env` template created
- [x] Hybrid parser set as default
- [x] Missing fields display implemented

---

## 🚀 Backend Deployment

### Choose Your Platform
- [ ] Railway (Recommended - easiest)
- [ ] Render (Good free tier)
- [ ] Fly.io (More control)
- [ ] Heroku (Paid only)
- [ ] Custom VPS (Most control)

### Deployment Steps
- [ ] Create account on chosen platform
- [ ] Connect GitHub repository
- [ ] Configure build settings
- [ ] Set start command: `uvicorn physics_diagram.api:app --host 0.0.0.0 --port $PORT`
- [ ] Deploy and wait for build
- [ ] Copy backend URL

### Environment Variables
- [ ] `PORT` - Auto-set by most platforms
- [ ] `ALLOWED_ORIGINS` - Set to your frontend URL (important!)
- [ ] `PYTHON_VERSION` - Set to 3.14 (optional)

### Verification
- [ ] Backend URL accessible
- [ ] GET `/` returns 404 (normal, means it's running)
- [ ] POST `/solve` accepts requests
- [ ] No errors in platform logs

---

## 🎨 Frontend Deployment

### Choose Your Platform
- [ ] Vercel (Recommended - fastest)
- [ ] Netlify (Good alternative)
- [ ] GitHub Pages (Static only)
- [ ] Cloudflare Pages (Fast CDN)

### Deployment Steps
- [ ] Create account on chosen platform
- [ ] Import GitHub repository
- [ ] Set root directory to `frontend`
- [ ] Set build command to `npm run build`
- [ ] Set output directory to `dist`
- [ ] Deploy and wait for build
- [ ] Copy frontend URL

### Environment Variables
- [ ] `VITE_API_BASE` - Set to your backend URL (required!)
  - Example: `https://physicslens-api.railway.app`
  - Must include `https://`
  - No trailing slash

### Verification
- [ ] Frontend URL loads
- [ ] UI appears correctly
- [ ] No console errors
- [ ] Try generating a diagram

---

## 🔗 Connect Frontend & Backend

### CORS Configuration
- [ ] Add `ALLOWED_ORIGINS` environment variable in backend
- [ ] Value = your frontend URL(s)
- [ ] Multiple URLs separated by commas
- [ ] Redeploy backend if needed

### Test Connection
- [ ] Open frontend in browser
- [ ] Open browser dev tools (F12)
- [ ] Try generating a diagram
- [ ] Check Network tab for API call
- [ ] Should see 200 OK response
- [ ] No CORS errors in console

---

## 🧪 Testing

### Functionality Tests
- [ ] **Simple case**: "A 5kg block on a 30 degree incline"
  - Should work instantly
  - Diagram should appear
  - Check derived values display

- [ ] **Missing fields**: "A block slides down a ramp"
  - Should show error message
  - Should display missing fields alert
  - Alert should list: mass kg, incline angle deg

- [ ] **Complex case**: "A ball is thrown at 45 degrees with speed 20 m/s"
  - Should work (may be slow without Ollama)
  - Diagram should appear

### Performance Tests
- [ ] Page loads in < 3 seconds
- [ ] Simple diagram generates in < 1 second
- [ ] Error messages appear immediately
- [ ] No console errors or warnings

### Cross-Browser Tests
- [ ] Works in Chrome
- [ ] Works in Firefox
- [ ] Works in Safari
- [ ] Works on mobile

### Edge Cases
- [ ] Empty input shows appropriate error
- [ ] Very long input doesn't crash
- [ ] Special characters handled
- [ ] Unsupported scenarios show correct message

---

## 🛡️ Security

### CORS
- [ ] `ALLOWED_ORIGINS` set to specific domains
- [ ] Not using wildcard (`*`) in production
- [ ] HTTPS enforced on both frontend and backend

### Environment Variables
- [ ] No secrets in code
- [ ] All sensitive data in environment variables
- [ ] Environment variables not exposed to frontend (except VITE_ prefixed)

### Input Validation
- [ ] Backend validates input sizes
- [ ] Frontend handles API errors gracefully
- [ ] No unhandled exceptions

---

## 📊 Monitoring & Logs

### Backend Monitoring
- [ ] Know how to access backend logs
- [ ] Check for startup errors
- [ ] Monitor response times
- [ ] Watch for crashes

### Frontend Monitoring
- [ ] Check build logs
- [ ] Monitor for runtime errors
- [ ] Track load times

### Optional (Advanced)
- [ ] Set up error tracking (Sentry)
- [ ] Add analytics (Google Analytics)
- [ ] Configure uptime monitoring
- [ ] Set up log aggregation

---

## 🎯 Post-Deployment

### Documentation
- [ ] Update README with live URLs
- [ ] Document deployment process
- [ ] Note any platform-specific quirks
- [ ] Save login credentials securely

### Sharing
- [ ] Test all shared links
- [ ] Prepare demo scenarios
- [ ] Create screenshots/GIFs
- [ ] Share on social media (optional)

### Maintenance
- [ ] Know how to deploy updates
- [ ] Understand rollback process
- [ ] Monitor usage/costs
- [ ] Plan for scaling if needed

---

## 🎨 Optional Enhancements

### Custom Domain
- [ ] Purchase domain
- [ ] Configure DNS for backend (api.yourdomain.com)
- [ ] Configure DNS for frontend (yourdomain.com)
- [ ] Update environment variables
- [ ] Test with new domains

### Analytics
- [ ] Add Google Analytics
- [ ] Track diagram generations
- [ ] Monitor popular physics scenarios
- [ ] Track error rates

### Monitoring
- [ ] Set up Sentry for error tracking
- [ ] Configure uptime monitoring
- [ ] Set up alerts for downtime
- [ ] Create status page

### Performance
- [ ] Enable CDN (usually automatic)
- [ ] Optimize images (if any)
- [ ] Review bundle sizes
- [ ] Add caching headers

---

## 💰 Cost Tracking

### Free Tier Limits
**Railway**:
- [ ] $5/month credit
- [ ] ~500 hours uptime
- [ ] Monitor usage in dashboard

**Vercel**:
- [ ] 100 GB bandwidth/month
- [ ] Unlimited deployments
- [ ] Check usage in dashboard

**Render**:
- [ ] 750 hours/month free
- [ ] Services sleep after inactivity
- [ ] Monitor in dashboard

### What to Monitor
- [ ] Monthly bandwidth usage
- [ ] Compute hours used
- [ ] API request count
- [ ] Storage used

### Scaling Plan
- [ ] Define traffic thresholds
- [ ] Plan for paid tier if needed
- [ ] Consider caching strategies
- [ ] Optimize expensive operations

---

## 🆘 Troubleshooting Guide

### "Unable to reach API"
**Check**:
- [ ] `VITE_API_BASE` environment variable set correctly
- [ ] Backend is deployed and running
- [ ] Backend URL includes `https://`
- [ ] No typos in URLs
- [ ] Redeploy frontend after env var changes

### "CORS Error"
**Check**:
- [ ] `ALLOWED_ORIGINS` set in backend
- [ ] Frontend URL matches exactly (no trailing slash)
- [ ] Backend has redeployed after env var change
- [ ] Both using HTTPS

### "Build Failed"
**Check**:
- [ ] `requirements.txt` is complete and up-to-date
- [ ] `package.json` dependencies are correct
- [ ] Build commands are correct in platform settings
- [ ] No syntax errors in code
- [ ] Platform logs for specific error

### "Diagram not generating"
**Check**:
- [ ] Backend logs for errors
- [ ] API `/solve` endpoint responding
- [ ] Network tab in browser dev tools
- [ ] Response status codes
- [ ] Error messages in console

### "Slow response times"
**Consider**:
- [ ] Upgrade to paid tier
- [ ] Optimize parser performance
- [ ] Add caching
- [ ] Use CDN for frontend
- [ ] Host Ollama separately (if using LLM)

---

## ✅ Deployment Complete!

Once everything is checked:

- [ ] ✨ App is live and accessible
- [ ] 🔒 Security measures in place
- [ ] 📊 Monitoring configured
- [ ] 📝 Documentation updated
- [ ] 🎉 Ready to share!

**Your deployment URLs:**
- Frontend: _______________________________
- Backend: _______________________________

**Next steps:**
1. Share with friends and colleagues
2. Gather feedback
3. Monitor usage and performance
4. Plan future improvements

---

## 📞 Support Resources

- **Railway**: https://railway.app/help
- **Vercel**: https://vercel.com/support
- **Render**: https://render.com/docs
- **FastAPI**: https://fastapi.tiangolo.com
- **Vite**: https://vitejs.dev

---

**Congratulations on your deployment! 🎉**

Remember: You can always redeploy by simply pushing to GitHub. Both platforms automatically rebuild and deploy your changes.
