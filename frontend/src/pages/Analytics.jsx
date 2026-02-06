import React, { useState, useEffect } from 'react';
import { Box, Typography } from '@mui/material';
import AnalyticsDashboard from '../components/AnalyticsDashboard';

const AnalyticsPage = () => {
    const [riskData, setRiskData] = useState(null);

    useEffect(() => {
        fetchRiskData();
        const interval = setInterval(fetchRiskData, 10000);
        return () => clearInterval(interval);
    }, []);

    const fetchRiskData = async () => {
        try {
            const response = await fetch('http://localhost:8000/analytics/dashboard');
            const data = await response.json();
            setRiskData(data);
        } catch (error) {
            console.error('Error fetching risk data:', error);
        }
    };

    return (
        <Box>
            <Typography variant="h5" color="text.primary" sx={{ mb: 3, letterSpacing: '0.05em' }}>
                INTELLIGENCE ANALYTICS
            </Typography>
            <AnalyticsDashboard data={riskData} />
        </Box>
    );
};

export default AnalyticsPage;
