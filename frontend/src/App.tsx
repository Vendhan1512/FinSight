import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { Login } from './pages/Login';
import { Overview } from './pages/Overview';
import { SystemStatus } from './pages/SystemStatus';

import { AssetIntelligence } from './pages/AssetIntelligence';

import { NewsIntelligence } from './pages/NewsIntelligence';

import { Predictions } from './pages/Predictions';

import { RiskAnalysis } from './pages/RiskAnalysis';
import { DataStateIndicator } from './components/ui/DataStateIndicator';

// Protected Route Wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="min-h-screen bg-background flex items-center justify-center text-textMain">Loading App...</div>;
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

// Placeholder components for unimplemented pages
const Placeholder = ({ title }: { title: string }) => (
  <div className="flex flex-col items-center justify-center h-64 text-textMuted border border-white/5 rounded-xl border-dashed">
    <p className="text-xl font-semibold mb-2">{title}</p>
    <p className="text-sm">This module is under active development.</p>
    <div className="mt-4"><DataStateIndicator state="UNAVAILABLE" /></div>
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route path="/" element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }>
            <Route index element={<Overview />} />
            <Route path="asset/:ticker" element={<AssetIntelligence />} />
            <Route path="predictions" element={<Predictions />} />
            <Route path="risk" element={<RiskAnalysis />} />
            <Route path="news" element={<NewsIntelligence />} />
            <Route path="explainability" element={<Placeholder title="Explainability" />} />
            <Route path="portfolio" element={<Placeholder title="Portfolio Management" />} />
            <Route path="data-quality" element={<Placeholder title="Data Quality" />} />
            <Route path="models" element={<Placeholder title="Model Registry" />} />
            <Route path="system" element={<SystemStatus />} />
          </Route>
          
          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
