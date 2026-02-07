import React, { useState, useEffect } from 'react';
import { Grid, Typography, Paper, Box, useTheme, Chip, IconButton } from '@mui/material';
import RiskHeatmap from '../components/RiskHeatmap';
import AlertQueue from '../components/AlertQueue';
import LiveFeed from '../components/LiveFeed';
import AnalyticsDashboard from '../components/AnalyticsDashboard';
import { motion } from 'framer-motion';
import { Activity, Shield, AlertTriangle, MoreHorizontal } from 'lucide-react';

const Dashboard = () => {
    const [alerts, setAlerts] = useState([]);
    const [riskData, setRiskData] = useState(null);
    const theme = useTheme();

    useEffect(() => {
        fetchAlerts();
        fetchRiskData();
        const interval = setInterval(() => {
            fetchAlerts();
            fetchRiskData();
        }, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchAlerts = async () => {
        try {
            const response = await fetch('http://localhost:8000/alerts/recent');
            const data = await response.json();
            setAlerts(data.alerts);
        } catch (error) { console.error('Error fetching alerts:', error); }
    };

    const fetchRiskData = async () => {
        try {
            const response = await fetch('http://localhost:8000/analytics/dashboard');
            const data = await response.json();
            setRiskData(data);
        } catch (error) { console.error('Error fetching risk data:', error); }
    };

    const cardVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
    };

    return (
        <Grid container spacing={4}>
            {/* Header Area */}
            <Grid item xs={12}>
                <Box sx={{ mb: 1 }}>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: theme.palette.text.primary, mb: 1 }}>
                        Overview
                    </Typography>
                    <Typography variant="body1" sx={{ color: theme.palette.text.secondary }}>
                        Live monitoring and safety analytics.
                    </Typography>
                </Box>
            </Grid>

            {/* Top Row: Map and Live Feed */}
            <Grid item xs={12} lg={8}>
                <motion.div variants={cardVariants} initial="hidden" animate="visible">
                    <Paper sx={{
                        p: 0,
                        height: 520,
                        display: 'flex',
                        flexDirection: 'column',
                        overflow: 'hidden'
                    }}>
                        {/* Clean Header */}
                        <Box sx={{
                            p: 3,
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                        }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                                <Box sx={{ p: 1, bgcolor: '#F0FDF4', borderRadius: '50%' }}> {/* Soft green bg */}
                                    <Activity size={20} color={theme.palette.primary.main} />
                                </Box>
                                <Typography variant="h6" sx={{ fontSize: '1rem', color: theme.palette.text.primary }}>
                                    Live Activity Map
                                </Typography>
                            </Box>
                            <Chip label="Active" size="small" color="success" sx={{ height: 24, fontSize: '0.75rem' }} />
                        </Box>

                        <Box sx={{ flexGrow: 1, position: 'relative' }}>
                            <RiskHeatmap alerts={alerts} />
                        </Box>
                    </Paper>
                </motion.div>
            </Grid>

            <Grid item xs={12} lg={4}>
                <motion.div variants={cardVariants} initial="hidden" animate="visible" transition={{ delay: 0.2 }}>
                    <Paper sx={{ p: 0, height: 520, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                        <Box sx={{
                            p: 3,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1.5,
                        }}>
                            <Box sx={{ p: 1, bgcolor: '#FFF7ED', borderRadius: '50%' }}> {/* Soft orange bg */}
                                <Shield size={20} color={theme.palette.secondary.main} />
                            </Box>
                            <Typography variant="h6" sx={{ fontSize: '1rem', color: theme.palette.text.primary }}>
                                Camera Feed
                            </Typography>
                        </Box>
                        <Box sx={{ flexGrow: 1, bgcolor: '#000', position: 'relative' }}>
                            <LiveFeed />
                        </Box>
                    </Paper>
                </motion.div>
            </Grid>

            {/* Middle Row: Analytics */}
            <Grid item xs={12}>
                <motion.div variants={cardVariants} initial="hidden" animate="visible" transition={{ delay: 0.3 }}>
                    <AnalyticsDashboard data={riskData} />
                </motion.div>
            </Grid>

            {/* Bottom Row: Alert Queue */}
            <Grid item xs={12}>
                <motion.div variants={cardVariants} initial="hidden" animate="visible" transition={{ delay: 0.4 }}>
                    <Paper sx={{ p: 0, overflow: 'hidden' }}>
                        <Box sx={{
                            p: 3,
                            borderBottom: `1px solid ${theme.palette.divider}`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between'
                        }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                                <Box sx={{ p: 1, bgcolor: '#FEF2F2', borderRadius: '50%' }}> {/* Soft red bg */}
                                    <AlertTriangle size={20} color={theme.palette.error.main} />
                                </Box>
                                <Typography variant="h6" sx={{ fontSize: '1rem', color: theme.palette.text.primary }}>
                                    Recent Alerts
                                </Typography>
                            </Box>
                            <IconButton size="small"><MoreHorizontal size={20} /></IconButton>
                        </Box>
                        <Box sx={{ p: 0 }}>
                            <AlertQueue alerts={alerts} onAcknowledge={fetchAlerts} />
                        </Box>
                    </Paper>
                </motion.div>
            </Grid>
        </Grid>
    );
};

export default Dashboard;
