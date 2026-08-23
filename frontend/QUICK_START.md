# ⚡ KneeVision AI - Quick Start

## 🚀 Start the Application

### Terminal 1 - Backend
```powershell
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 - Frontend
```powershell
npm run dev
```

### Open Browser
```
http://localhost:5173
(or whatever port Vite displays)
```

---

## ✅ Everything Working When You See:

**Backend Terminal:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

**Frontend Terminal:**
```
VITE v5.4.21  ready in XXX ms
➜  Local:   http://localhost:5XXX/
```

**Browser:**
- Dashboard loads with patient statistics
- No error messages
- Charts display data

---

## 🐛 Quick Fixes

### "Failed to fetch analytics"
**Solution:**
1. Refresh browser (F5)
2. If still broken: Restart backend (Ctrl+C, then restart)
3. If still broken: Restart frontend (Ctrl+C, then restart)

### Port Already in Use
**Frontend automatically finds next port** → This is normal!
- 5173 → 5174 → 5175 → 5176...

**Backend must stay on 8000** → Kill the other process:
```powershell
# Find process on port 8000
netstat -ano | findstr :8000

# Kill it (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Dashboard Not Loading
1. ✅ Backend running? Check terminal 1
2. ✅ Port 8000? Should see: `http://0.0.0.0:8000`
3. ✅ Test: `curl http://localhost:8000/health`
4. ✅ Hard refresh browser: Ctrl+F5

---

## 📋 Pre-Demo Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running (any port OK)
- [ ] Dashboard shows patient data
- [ ] Implant sizing accepts input
- [ ] Analytics displays charts
- [ ] No red errors in console (F12)
- [ ] Build passes: `npm run build`

---

## 🔗 Key URLs

- **Frontend:** http://localhost:5173 (or 5174/5175/5176)
- **Backend:** http://localhost:8000
- **API Health:** http://localhost:8000/health
- **API Analytics:** http://localhost:8000/analytics

---

## 💡 Pro Tips

1. **Keep both terminals open** while developing
2. **Auto-reload enabled** - save files to see changes
3. **Check backend logs** if frontend shows errors
4. **F12 → Console** to see frontend errors
5. **F12 → Network** to see API requests

---

## 🆘 Emergency Reset

If everything is broken:

```powershell
# Terminal 1 - Stop and restart backend
Ctrl+C
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Stop and restart frontend
Ctrl+C
npm run dev

# Browser - Hard refresh
Ctrl+F5
```

---

**Need more details?** See `DEVELOPMENT_GUIDE.md`
