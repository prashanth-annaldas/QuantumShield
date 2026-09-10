import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { LoadingSpinner } from './components/LoadingSpinner';

// Application Pages
import { ThreatLogs } from './pages/ThreatLogs';
import { CreateSignature } from './pages/CreateSignature';
import { TeleportationSim } from './pages/TeleportationSim';
import { SignatureVerification } from './pages/SignatureVerification';
import { AttackSimulator } from './pages/AttackSimulator';
import { ThreatDetection } from './pages/ThreatDetection';
import { SecurityOperations } from './pages/SecurityOperations';
import { IncidentCenter } from './pages/IncidentCenter';
import { SessionTimeline } from './pages/SessionTimeline';
import { SystemMonitoring } from './pages/SystemMonitoring';
import { SecurityAudit } from './pages/SecurityAudit';
import { ProductionReadiness } from './pages/ProductionReadiness';
import { Login } from './pages/Login';
import { Register } from './pages/Register';

// Protected Route Guard Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <LoadingSpinner label="Validating Security Credentials..." size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

// Role Guard for Analyst and Admin Only
const AnalystOrAdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  if (user && user.role !== 'ADMIN' && user.role !== 'SECURITY_ANALYST') {
    return <Navigate to="/create-signature" replace />;
  }
  return <>{children}</>;
};

// Main Layout Shell with Sidebar and Navbar
const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.innerWidth >= 1024;
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex font-sans">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div
        className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ease-in-out ${
          sidebarOpen ? 'lg:pl-64' : 'pl-0'
        }`}
      >
        <Navbar
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          isSidebarOpen={sidebarOpen}
        />

        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Auth Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Application Routes */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <Routes>
                    <Route path="/" element={<Navigate to="/create-signature" replace />} />
                    <Route path="/create-signature" element={<CreateSignature />} />
                    <Route path="/teleportation" element={<TeleportationSim />} />
                    <Route path="/verification" element={<SignatureVerification />} />
                    <Route path="/attack-simulator" element={<AttackSimulator />} />
                    <Route path="/threat-detection" element={<ThreatDetection />} />
                    <Route path="/threat-logs" element={<ThreatLogs />} />
                    <Route
                      path="/soc"
                      element={
                        <AnalystOrAdminRoute>
                          <SecurityOperations />
                        </AnalystOrAdminRoute>
                      }
                    />
                    <Route
                      path="/incidents"
                      element={
                        <AnalystOrAdminRoute>
                          <IncidentCenter />
                        </AnalystOrAdminRoute>
                      }
                    />
                    <Route path="/sessions/timeline" element={<SessionTimeline />} />
                    <Route
                      path="/monitoring"
                      element={
                        <AnalystOrAdminRoute>
                          <SystemMonitoring />
                        </AnalystOrAdminRoute>
                      }
                    />
                    <Route path="/audit" element={<SecurityAudit />} />
                    <Route
                      path="/readiness"
                      element={
                        <AnalystOrAdminRoute>
                          <ProductionReadiness />
                        </AnalystOrAdminRoute>
                      }
                    />
                    {/* Fallback route */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </AppLayout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;
