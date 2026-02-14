import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper } from '@mui/material';
import AlertQueue from '../components/AlertQueue';
import { API_BASE_URL } from '../config';

const AlertsPage = () => {
    const [alerts, setAlerts] = useState([]);

    useEffect(() => {
        fetchAlerts();
        const interval = setInterval(fetchAlerts, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchAlerts = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/alerts/recent?limit=100`);
            const data = await response.json();
            setAlerts(data.alerts);
        } catch (error) {
            console.error('Error fetching alerts:', error);
        }
    };

    return (
        <Box>
            <Typography variant="h5" color="text.primary" sx={{ mb: 3, letterSpacing: '0.05em' }}>
                SYSTEM ALERT LOG
            </Typography>
            <Paper sx={{ p: 3 }}>
                <AlertQueue alerts={alerts} onAcknowledge={fetchAlerts} />
            </Paper>
        </Box>
    );
};

export default AlertsPage;
