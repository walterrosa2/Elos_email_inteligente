import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import { Login } from './pages/Login';
import { DashboardLayout } from './layouts/DashboardLayout';
import { Dashboard } from './pages/Dashboard';
import { Analysis } from './pages/Analysis';
import { Contracts } from './pages/Contracts';
import { Settings } from './pages/Settings';
import { Schedule } from './pages/Schedule';
import { Reports } from './pages/Reports';

const AuthGuard = ({ children, requireAdmin }: { children: React.ReactNode, requireAdmin?: boolean }) => {
  const { user, token } = useAuthStore();
  
  if (!token || !user) {
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && user.role !== 'admin') {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        <Route element={<AuthGuard><DashboardLayout /></AuthGuard>}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/contracts" element={<AuthGuard requireAdmin><Contracts /></AuthGuard>} />
          <Route path="/settings" element={<AuthGuard requireAdmin><Settings /></AuthGuard>} />
          <Route path="/schedule" element={<AuthGuard><Schedule /></AuthGuard>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
