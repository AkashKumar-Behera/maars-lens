import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import NotFound from './components/NotFound';
import AuthPage from './pages/AuthPage';

// Officer Pages
import OfficerDashboard from './pages/officer/OfficerDashboard';
import NewInspection from './pages/officer/NewInspection';
import InspectionDetails from './pages/officer/InspectionDetails';
import InspectionHistory from './pages/officer/InspectionHistory';
import ViolationsList from './pages/officer/ViolationsList';

// Admin Pages
import AdminDashboard from './pages/admin/AdminDashboard';
import UserManagement from './pages/admin/UserManagement';

// Common / Shared Pages
import RulesBrowser from './pages/common/RulesBrowser';

// Retailer & Customer Pages
import RetailerDashboard from './pages/retailer/RetailerDashboard';
import CustomerPortal from './pages/customer/CustomerPortal';

function App() {
  const { loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400 text-sm">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500 mr-3" />
        Initializing MAARS Lens Secure Session...
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<AuthPage initialMode="login" />} />
        <Route path="/register" element={<AuthPage initialMode="register" />} />

        {/* Officer Route Hierarchy */}
        <Route 
          path="/officer/*" 
          element={
            <ProtectedRoute role="officer">
              <Layout>
                <Routes>
                  <Route path="/" element={<OfficerDashboard />} />
                  <Route path="/new-inspection" element={<NewInspection />} />
                  <Route path="/inspections" element={<InspectionHistory />} />
                  <Route path="/inspections/:id" element={<InspectionDetails />} />
                  <Route path="/violations" element={<ViolationsList />} />
                  <Route path="/rules" element={<RulesBrowser />} />
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          } 
        />

        {/* Admin Route Hierarchy */}
        <Route 
          path="/admin/*" 
          element={
            <ProtectedRoute role="admin">
              <Layout>
                <Routes>
                  <Route path="/" element={<AdminDashboard />} />
                  <Route path="/scan" element={<NewInspection />} />
                  <Route path="/officers" element={<UserManagement initialRole="officer" />} />
                  <Route path="/users" element={<UserManagement initialRole="all" />} />
                  <Route path="/inspections" element={<InspectionHistory />} />
                  <Route path="/inspections/:id" element={<InspectionDetails />} />
                  <Route path="/violations" element={<ViolationsList />} />
                  <Route path="/rules" element={<RulesBrowser />} />
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          } 
        />

        {/* Retailer Route Hierarchy */}
        <Route 
          path="/retailer/*" 
          element={
            <ProtectedRoute role="retailer">
              <Layout>
                <Routes>
                  <Route path="/" element={<RetailerDashboard />} />
                  <Route path="/inspections" element={<InspectionHistory />} />
                  <Route path="/inspections/:id" element={<InspectionDetails />} />
                  <Route path="/rules" element={<RulesBrowser />} />
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          } 
        />

        {/* Customer Route Hierarchy */}
        <Route 
          path="/customer/*" 
          element={
            <ProtectedRoute role="customer">
              <Layout>
                <Routes>
                  <Route path="/" element={<CustomerPortal />} />
                  <Route path="/rules" element={<RulesBrowser />} />
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          } 
        />

        {/* Default redirects */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}

export default App;
