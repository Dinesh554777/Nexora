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

This is Phase 1 of the KneeVision AI hackathon project. The current implementation includes:

- ✅ Complete frontend foundation with responsive design
- ✅ Professional medical-grade UI/UX
- ✅ Demo data for visualization and testing
- ✅ Component architecture ready for API integration

Future phases will include:
- Backend API integration
- Machine learning model integration
- Real-time image analysis
- Patient data management system

## License

This is a hackathon project for demonstration purposes.
