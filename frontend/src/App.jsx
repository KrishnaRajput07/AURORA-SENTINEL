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

function App() {
    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <Router>
                <Layout>
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/surveillance" element={<LiveSurveillance />} />
                        <Route path="/demo" element={<DemoAnalysis />} />
                        <Route path="/alerts" element={<AlertsPage />} />
                        <Route path="/analytics" element={<AnalyticsPage />} />
                        <Route path="/system" element={<SystemPage />} />
                    </Routes>
                </Layout>
            </Router>
        </ThemeProvider>
    );
}

export default App;
