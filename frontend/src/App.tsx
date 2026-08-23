import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { Dashboard } from './pages/Dashboard';
import { ImplantSizing } from './pages/ImplantSizing';
import { MedicalImaging } from './pages/MedicalImaging';
import { ProgressView } from './pages/ProgressView';
import { OAAnalytics } from './pages/OAAnalytics';
import { Settings } from './pages/Settings';
import { DemoCases } from './pages/DemoCases';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="implant-sizing" element={<ImplantSizing />} />
          <Route path="medical-imaging" element={<MedicalImaging />} />
          <Route path="progress-view" element={<ProgressView />} />
          <Route path="oa-analytics" element={<OAAnalytics />} />
          <Route path="settings" element={<Settings />} />
          <Route path="demo-cases" element={<DemoCases />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
