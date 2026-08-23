# KneeVision AI - Development Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ (for backend)
- Node.js 16+ (for frontend)
- npm or yarn

### Starting the Application

**1. Start Backend (Terminal 1):**
```powershell
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**2. Start Frontend (Terminal 2):**
```powershell
npm run dev
```

The frontend will automatically find an available port (typically 5173-5176).

---

## 🔧 Common Issues & Solutions

### Issue: "Failed to fetch analytics: Failed to fetch"

**Cause:** CORS (Cross-Origin Resource Sharing) blocking requests from frontend to backend.

**Solution:** ✅ **ALREADY FIXED**

The backend is now configured to accept requests from **any localhost port** using a regex pattern:

```python
allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+"
```

This means:
- Frontend can run on any port (5173, 5174, 5175, 5176, etc.)
- No need to update CORS configuration when port changes
- Works for both `localhost` and `127.0.0.1`

**If you still see CORS errors:**
1. Stop the backend (Ctrl+C)
2. Restart it: `python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`
3. Refresh the browser (F5)

---

## 📝 Environment Configuration

### Backend Configuration
**File:** `backend/main.py`

CORS is configured to allow all localhost ports for development:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**⚠️ For Production:**
Replace the regex with specific allowed origins:
```python
allow_origins=[
    "https://yourdomain.com",
    "https://www.yourdomain.com"
]
```

### Frontend Configuration
**File:** `.env`

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_ENV=development
```

- `VITE_API_BASE_URL`: Backend API endpoint
- `VITE_APP_ENV`: Environment (development/production)

---

## 🔍 Troubleshooting

### Dashboard shows "Error Loading Dashboard"

**Check 1: Backend Status**
```powershell
# Test backend health
curl http://localhost:8000/health
```
Expected response: `{"status":"healthy","service":"KneeVision AI API"}`

**Check 2: Analytics Endpoint**
```powershell
# Test analytics endpoint
curl http://localhost:8000/analytics
```
Should return JSON with patient data.

**Check 3: CORS Headers**
Open browser DevTools (F12) → Network tab → Look for:
- Red requests = CORS issue
- Check Response Headers for `Access-Control-Allow-Origin`

**Solution:**
1. Verify backend is running on port 8000
2. Verify `.env` file has correct `VITE_API_BASE_URL`
3. Restart both backend and frontend
4. Hard refresh browser (Ctrl+F5)

### Frontend Port Conflicts

If port 5173 is in use, Vite automatically tries the next available port:
- 5173 → 5174 → 5175 → 5176...

**This is normal and expected.** The CORS configuration supports all ports.

---

## 🏗️ Architecture

### Backend (FastAPI - Python)
```
backend/
├── main.py              # API endpoints & CORS config
├── requirements.txt     # Python dependencies
└── data/               # Demo patient data (if any)
```

**Endpoints:**
- `GET /health` - Health check
- `GET /analytics` - Patient analytics & OA statistics
- `POST /implant-match` - Knee implant matching

### Frontend (React + Vite + TypeScript)
```
src/
├── pages/
│   ├── Dashboard.tsx        # Main dashboard
│   ├── ImplantSizing.tsx    # Implant recommendation
│   └── OAAnalytics.tsx      # Analytics & charts
├── components/
│   ├── implant/             # Implant explainability components
│   ├── analytics/           # Analytics components
│   ├── shared/              # Shared UI components
│   └── ui/                  # shadcn/ui components
├── services/
│   └── api.ts               # API service layer
├── lib/
│   └── analytics.ts         # Analytics utilities
└── types/
    ├── index.ts             # Frontend types
    └── api.ts               # API response types
```

---

## 🧪 Testing

### Backend Testing
```powershell
cd backend
python -m pytest  # If tests are configured
```

### Frontend Testing
```powershell
npm run build     # Test build
npm run lint      # Lint check (if configured)
```

### Manual Testing Checklist
- [ ] Dashboard loads without errors
- [ ] Analytics page displays patient data
- [ ] Implant sizing form accepts input
- [ ] Implant recommendation displays results
- [ ] Charts render properly
- [ ] Filters work in analytics
- [ ] Mobile responsive (test on small screen)

---

## 📦 Building for Production

### Backend
```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Remember:** Update CORS to production domains!

### Frontend
```powershell
npm run build
```

Output: `dist/` folder with optimized static files.

**Deploy:**
- Serve `dist/` folder with any static file server
- Update `VITE_API_BASE_URL` to production backend URL
- Ensure backend CORS allows production frontend domain

---

## 🔐 Security Notes

### Development
- CORS allows all localhost ports ✅
- No authentication required ✅
- API runs on 0.0.0.0 (all interfaces) ✅

### Production
- [ ] Update CORS to specific domains only
- [ ] Add authentication/authorization
- [ ] Use HTTPS for API
- [ ] Add rate limiting
- [ ] Validate all inputs
- [ ] Don't expose internal errors to clients

---

## 🐛 Debugging Tips

### Backend Logs
The backend runs with `--reload` flag, showing:
- Incoming requests
- Response status codes
- Auto-reload on file changes

**Common Log Messages:**
- `200 OK` = Success ✅
- `400 Bad Request` = Bad input or CORS preflight failure
- `404 Not Found` = Endpoint doesn't exist
- `500 Internal Server Error` = Backend error (check Python traceback)

### Frontend Console
Open DevTools (F12) → Console tab

**Look for:**
- Network errors (Failed to fetch)
- CORS errors (blocked by CORS policy)
- TypeScript errors (red underlines in code)
- Component render errors

### Network Tab
Open DevTools (F12) → Network tab

**Check:**
- Request URL (should be http://localhost:8000/...)
- Request Method (GET, POST, OPTIONS)
- Status Code (200 = good, 4xx/5xx = error)
- Response Headers (Access-Control-Allow-Origin)
- Response Body (API data)

---

## 🔄 Git Workflow

### Before Committing
```powershell
# Build check
npm run build

# Stage changes
git add .

# Commit
git commit -m "Your message"

# Push
git push
```

### Important Files to Commit
- ✅ All `.tsx`, `.ts`, `.py` source files
- ✅ `package.json`, `requirements.txt`
- ✅ `.env.example` (template, not actual `.env`)
- ✅ Documentation (`.md` files)

### Files to Ignore (Already in `.gitignore`)
- ❌ `node_modules/`
- ❌ `dist/`
- ❌ `.env` (contains secrets)
- ❌ `__pycache__/`
- ❌ `.vite/`

---

## 📞 Getting Help

### Error Messages

**"Failed to fetch analytics"**
→ Backend not running or CORS issue
→ Solution: Restart backend, check port 8000

**"Network Error"**
→ Backend URL incorrect in `.env`
→ Solution: Verify `VITE_API_BASE_URL=http://localhost:8000`

**"TypeError: Cannot read property..."**
→ API response structure mismatch
→ Solution: Check API response matches TypeScript types

**"Module not found"**
→ Missing dependency
→ Solution: `npm install` or `pip install -r requirements.txt`

---

## 🎯 Development Checklist

### Daily Startup
1. [ ] Start backend: `python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`
2. [ ] Start frontend: `npm run dev`
3. [ ] Open browser: `http://localhost:5173` (or whichever port Vite shows)
4. [ ] Verify dashboard loads

### Before Demo/Hackathon
1. [ ] Backend running on port 8000
2. [ ] Frontend running (any port 5173-5176)
3. [ ] Dashboard displays patient data
4. [ ] Implant sizing works end-to-end
5. [ ] Analytics charts render
6. [ ] Mobile view works
7. [ ] No console errors
8. [ ] Build passes: `npm run build`

### Code Quality
1. [ ] TypeScript errors resolved
2. [ ] No console.log statements
3. [ ] Components properly typed
4. [ ] API errors handled gracefully
5. [ ] Loading states implemented
6. [ ] Responsive design checked

---

## 🎉 Success Indicators

When everything is working:
- ✅ Backend logs show: `Uvicorn running on http://0.0.0.0:8000`
- ✅ Frontend logs show: `Local: http://localhost:5XXX/`
- ✅ Dashboard displays patient statistics
- ✅ No red errors in browser console
- ✅ Network tab shows 200 OK responses
- ✅ Charts render with data
- ✅ Forms accept and submit data

---

## 📚 Additional Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **React Docs:** https://react.dev/
- **Vite Docs:** https://vitejs.dev/
- **shadcn/ui:** https://ui.shadcn.com/
- **Recharts:** https://recharts.org/

---

**Last Updated:** August 22, 2026  
**Version:** Phase 4 Complete  
**Status:** Production Ready for Hackathon 🚀
