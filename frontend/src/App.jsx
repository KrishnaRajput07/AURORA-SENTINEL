import React from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import theme from './theme';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import LiveSurveillance from './pages/LiveSurveillance';
import AlertsPage from './pages/Alerts';
import AnalyticsPage from './pages/Analytics';
import SystemPage from './pages/System';
import Intelligence from './pages/Intelligence';
import ArchivesPage from './pages/Archives';
import Login from './pages/Login';
import AdminDashboard from './pages/AdminDashboard';
import NetworkStatusIndicator from './components/NetworkStatusIndicator';
import { AuthProvider, useAuth } from './context/AuthContext';

const ProtectedRoute = ({ children, roles }) => {
    const { user, loading } = useAuth();
    if (loading) return null;
    if (!user) return <Navigate to="/login" replace />;
    if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
    return children;
};

function AppContent() {
    return (
        <Routes>
            <Route path="/login" element={<Login />} />

            <Route path="/" element={
                <ProtectedRoute>
                    <Layout><Dashboard /></Layout>
                </ProtectedRoute>
            } />

            <Route path="/admin" element={
                <ProtectedRoute roles={['admin']}>
                    <Layout><AdminDashboard /></Layout>
                </ProtectedRoute>
            } />

            <Route path="/surveillance" element={
                <ProtectedRoute>
                    <Layout><LiveSurveillance /></Layout>
                </ProtectedRoute>
            } />

            <Route path="/intelligence" element={
                <ProtectedRoute>
                    <Layout><Intelligence /></Layout>
                </ProtectedRoute>
            } />

            <Route path="/archives" element={
                <ProtectedRoute>
                    <Layout><ArchivesPage /></Layout>
                </ProtectedRoute>
            } />

            <Route path="/alerts" element={
                <ProtectedRoute>
                    <Layout><AlertsPage /></Layout>
                </ProtectedRoute>
            } />

            <Route path="/analytics" element={
                <ProtectedRoute>
                    <Layout><AnalyticsPage /></Layout>
                </ProtectedRoute>
            } />

            <Route path="/system" element={
                <ProtectedRoute>
                    <Layout><SystemPage /></Layout>
                </ProtectedRoute>
            } />
        </Routes>
    );
}

function App() {
    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <AuthProvider>
                <NetworkStatusIndicator />
                <AppContent />
            </AuthProvider>
        </ThemeProvider>
    );
}

export default App;
