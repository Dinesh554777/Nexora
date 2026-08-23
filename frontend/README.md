# KneeVision AI

An AI-assisted knee imaging platform for orthopedic analysis, featuring medial meniscus measurement, osteoarthritis analysis, and patient-specific knee implant sizing.

## Features

- **Clinical Dashboard**: Overview of patient analytics and recent analyses
- **Implant Sizing**: AI-powered knee implant recommendation based on patient measurements
- **OA Analytics**: Comprehensive osteoarthritis analytics with interactive visualizations
- **Responsive Design**: Professional medical-grade UI that works on desktop, tablet, and mobile

## Tech Stack

- **Frontend**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **Charts**: Recharts
- **Routing**: React Router
- **Icons**: Lucide React

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The application will be available at `http://localhost:5173/`

## Project Structure

```
src/
├── components/
│   ├── ui/              # Reusable UI components (shadcn/ui)
│   ├── layout/          # Layout components (Navbar, Sidebar, etc.)
│   ├── shared/          # Shared components (PageHeader, etc.)
│   ├── dashboard/       # Dashboard-specific components
│   ├── implant/         # Implant sizing components
│   └── analytics/       # Analytics components
├── pages/               # Page components
├── data/                # Demo data and utilities
├── types/               # TypeScript type definitions
├── lib/                 # Utility functions
└── hooks/               # Custom React hooks

## Routes

- `/dashboard` - Clinical dashboard overview
- `/implant-sizing` - Implant sizing and recommendation
- `/oa-analytics` - OA analytics and patient data
- `/settings` - Application settings

## Development Notes

This project has completed all phases:

- ✅ Phase 0: Project setup and configuration
- ✅ Phase 1: Complete frontend foundation with responsive design
- ✅ Phase 2: Backend API integration with ML-powered features
- ✅ Phase 3: Clinical workflow & hackathon polish
- ✅ Phase 4: AI explainability & clinical decision support
- ✅ Professional medical-grade UI/UX
- ✅ Real-time API integration
- ✅ ML-based implant matching algorithm
- ✅ Comprehensive OA analytics with explainability
- ✅ Component architecture with full API integration
- ✅ CORS configured for development (all localhost ports supported)

### Running the Full Application

**Start Backend (Terminal 1):**
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Start Frontend (Terminal 2):**
```bash
npm run dev
```

Visit the URL shown in the terminal (typically `http://localhost:5173/` or similar)

API Documentation: `http://localhost:8000/docs`

**⚠️ Important:** The backend CORS is configured to accept requests from any localhost port using regex pattern. This means the frontend can run on any port (5173, 5174, 5175, 5176, etc.) without CORS issues.

**Quick Start:** See [QUICK_START.md](./QUICK_START.md) for instant setup  
**Full Guide:** See [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) for comprehensive documentation

## Phase 2 Features

### Backend API
- **FastAPI** server with 4 endpoints
- **ML Algorithm**: Euclidean distance-based implant matching
- **OA Analytics**: Comprehensive patient statistics
- **Data Models**: 15 demo patients, 5 reference implants
- **CORS**: Configured for local development

### Frontend Integration
- **API Service Layer**: Centralized, typed API calls
- **Real-time Data**: Dashboard and analytics from live API
- **Form Validation**: Client-side validation before API calls
- **Error Handling**: Professional error messages and retry logic
- **Loading States**: Skeleton loaders and progress indicators

See [INTEGRATION.md](./INTEGRATION.md) for complete Phase 2 documentation.

## License

This is a hackathon project for demonstration purposes.
