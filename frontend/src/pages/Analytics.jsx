import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Divider } from '@mui/material';
import AnalyticsDashboard from '../components/AnalyticsDashboard';
import AlertQueue from '../components/AlertQueue';
import { BarChart2 } from 'lucide-react';
import { API_BASE_URL } from '../config';

const AnalyticsPage = () => {
    const [riskData, setRiskData] = useState(null);
    const [alerts, setAlerts] = useState([]);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            const [riskRes, alertsRes] = await Promise.all([
                fetch(`${API_BASE_URL}/analytics/dashboard`),
                fetch(`${API_BASE_URL}/alerts/recent`)
            ]);

            const rData = await riskRes.json();
            const aData = await alertsRes.json();

            setRiskData(rData);
            setAlerts(aData.alerts);
        } catch (error) {
            console.error('Error fetching analytics:', error);
        }
    };

    return (
        <Box>
            <Box sx={{ mb: 3 }}>
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#1A202C', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <BarChart2 size={28} color="#4A5568" />
                    Intelligence Analytics
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Real-time threat assessment and historical alert logs.
                </Typography>
            </Box>

            {/* Top Section: Charts & Stats */}
            <Box sx={{ mb: 4 }}>
                <AnalyticsDashboard data={riskData} />
            </Box>

            <Divider sx={{ my: 4 }} />

            {/* Bottom Section: Detailed Logs */}
            <Box>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, color: '#2D3748' }}>
                    Alert Queue History
                </Typography>
                <Paper sx={{ borderRadius: 2, border: '1px solid #E2E8F0', overflow: 'hidden', boxShadow: '0 2px 4px rgba(0,0,0,0.02)' }}>
                    <AlertQueue alerts={alerts} onAcknowledge={fetchData} />
                </Paper>
            </Box>
        </Box>
    );
};

export default AnalyticsPage;
