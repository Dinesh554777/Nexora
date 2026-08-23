# KneeVision AI - Quick Start Guide

Get KneeVision AI running in 3 minutes.

## Prerequisites

- Node.js 18+ installed
- Python 3.8+ installed
- Git (optional, for cloning)

## Step 1: Install Dependencies

### Frontend Dependencies
```bash
npm install
```

### Backend Dependencies
```bash
cd backend
pip install fastapi uvicorn pydantic pandas numpy scikit-learn python-multipart
cd ..
```

Or use requirements.txt:
```bash
cd backend
pip install -r requirements.txt
cd ..
```

## Step 2: Start the Backend

Open a terminal and run:
```bash
cd backend
python -m uvicorn main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

✅ Backend is now running on `http://localhost:8000`

Test it: Open `http://localhost:8000/docs` in your browser to see the API documentation.

## Step 3: Start the Frontend

Open a **new terminal** and run:
```bash
npm run dev
```

You should see:
```
VITE v5.4.21  ready in 335 ms
➜  Local:   http://localhost:5173/
```

✅ Frontend is now running on `http://localhost:5173`

## Step 4: Use the Application

Open your browser and navigate to `http://localhost:5173/`

### Try These Features:

**1. Dashboard**
- View patient analytics and KPI metrics
- See recent analysis results
- Check OA overview

**2. Implant Sizing**
- Click "Implant Sizing" in the sidebar
- Enter patient measurements:
  - Femur Width: 65.5
  - Femur AP: 58.2
  - Tibia Width: 72.3
  - Tibia AP: 48.7
- Click "Analyze Measurements"
- View the AI-powered implant recommendation
- See alternative implant options

**3. OA Analytics**
- Click "OA Analytics" in the sidebar
- Explore charts showing:
  - OA vs Non-OA distribution
  - Age group analysis
  - Sex-based patterns
  - Meniscus thickness correlation
- Search and filter patient records

## Troubleshooting

### Backend won't start
- Check if Python is installed: `python --version`
- Check if port 8000 is available
- Install missing packages: `pip install -r backend/requirements.txt`

### Frontend won't start
- Check if Node.js is installed: `node --version`
- Delete `node_modules` and run `npm install` again
- Check if port 5173 is available (Vite will use next available port)

### API errors in browser
- Make sure backend is running on port 8000
- Check browser console for CORS errors
- Verify `.env` file has: `VITE_API_BASE_URL=http://localhost:8000`

### CORS errors
- Make sure you're accessing frontend through the correct port (shown in terminal)
- Backend auto-reloads when code changes, check terminal for errors

## API Endpoints

Once backend is running, you can test endpoints directly:

### Health Check
```bash
GET http://localhost:8000/health
```

### Get Analytics
```bash
GET http://localhost:8000/analytics
```

### Match Implant
```bash
POST http://localhost:8000/implant-match
Content-Type: application/json

{
  "femurWidth": 65.5,
  "femurAP": 58.2,
  "tibiaWidth": 72.3,
  "tibiaAP": 48.7
}
```

## Build for Production

To create a production build:

```bash
npm run build
```

The built files will be in the `dist/` folder.

To preview the production build:

```bash
npm run preview
```

## What's Next?

- Explore the codebase in `src/` (frontend) and `backend/` (API)
- Read [INTEGRATION.md](./INTEGRATION.md) for technical details
- Check [README.md](./README.md) for full project documentation
- Customize the implant database in `backend/main.py`
- Add more patient data or modify analytics

## Getting Help

- Check the browser console for frontend errors
- Check the backend terminal for API errors
- Review `INTEGRATION.md` for API documentation
- Check FastAPI docs at `http://localhost:8000/docs`

---

**Congratulations!** 🎉 You now have KneeVision AI running with:
- ✅ Interactive dashboard
- ✅ AI-powered implant sizing
- ✅ Comprehensive OA analytics
- ✅ Real-time API integration
