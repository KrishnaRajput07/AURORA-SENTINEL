import React from 'react';
import { ThemeProvider, CssBaseline, Box } from '@mui/material';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import theme from './theme';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import LiveSurveillance from './pages/LiveSurveillance';
import DemoAnalysis from './pages/DemoAnalysis';
import AlertsPage from './pages/Alerts';
import AnalyticsPage from './pages/Analytics';
import SystemPage from './pages/System';
import IntelligencePage from './pages/DemoAnalysis'; // Temporary link to DemoAnalysis until new Intelligence.jsx is ready
import ArchivesPage from './pages/Archives';
import NetworkStatusIndicator from './components/NetworkStatusIndicator';

function App() {
    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <NetworkStatusIndicator />
            <Layout>
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/surveillance" element={<LiveSurveillance />} />
                    <Route path="/intelligence" element={<IntelligencePage />} />
                    <Route path="/archives" element={<ArchivesPage />} />
                    <Route path="/alerts" element={<AlertsPage />} />
                    <Route path="/analytics" element={<AnalyticsPage />} />
                    <Route path="/system" element={<SystemPage />} />
                </Routes>
            </Layout>
        </ThemeProvider>
    );
}

export default App;
