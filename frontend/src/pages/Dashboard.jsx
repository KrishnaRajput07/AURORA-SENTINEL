import React, { useState, useEffect } from 'react';
import { Grid, Typography, Paper, Box, useTheme, Chip } from '@mui/material';
import RiskHeatmap from '../components/RiskHeatmap';
import AlertQueue from '../components/AlertQueue';
import LiveFeed from '../components/LiveFeed';
import AnalyticsDashboard from '../components/AnalyticsDashboard';
import { motion } from 'framer-motion';
import { Activity, Radio, ShieldAlert } from 'lucide-react';

const Dashboard = () => {
    const [alerts, setAlerts] = useState([]);
    const [riskData, setRiskData] = useState(null);
    const muiTheme = useTheme();

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
        } catch (error) {
            console.error('Error fetching alerts:', error);
        }
    };

    const fetchRiskData = async () => {
        try {
            const response = await fetch('http://localhost:8000/analytics/dashboard');
            const data = await response.json();
            setRiskData(data);
        } catch (error) {
            console.error('Error fetching risk data:', error);
        }
    };

    const cardVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
    };

    return (
        <Grid container spacing={3}>
            {/* Top Row: Map and Live Feed */}
            <Grid item xs={12} lg={8}>
                <motion.div variants={cardVariants} initial="hidden" animate="visible">
                    <Paper sx={{
                        p: 0,
                        height: 500,
                        overflow: 'hidden',
                        display: 'flex',
                        flexDirection: 'column',
                        position: 'relative'
                    }}>
                        <Box sx={{
                            p: 2,
                            borderBottom: `1px solid ${muiTheme.palette.divider}`,
                            background: muiTheme.palette.action.hover,
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center'
                        }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                                <Activity size={20} color={muiTheme.palette.primary.main} />
                                <Typography variant="h6" color="text.primary">
                                    City Surveillance Grid
                                </Typography>
                            </Box>
                            <Chip
                                icon={<Radio size={14} />}
                                label="LIVE ACTIVITY"
                                color="success"
                                size="small"
                                variant="outlined"
                                sx={{ fontWeight: 600 }}
                            />
                        </Box>
                        <Box sx={{ flexGrow: 1, position: 'relative' }}>
                            <RiskHeatmap alerts={alerts} />
                        </Box>
                    </Paper>
                </motion.div>
            </Grid>

            <Grid item xs={12} lg={4}>
                <motion.div variants={cardVariants} initial="hidden" animate="visible" transition={{ delay: 0.2 }}>
                    <Paper sx={{ p: 0, height: 500, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                        <Box sx={{
                            p: 2,
                            borderBottom: `1px solid ${muiTheme.palette.divider}`,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1.5
                        }}>
                            <ShieldAlert size={20} color={muiTheme.palette.secondary.main} />
                            <Typography variant="h6" color="text.primary">
                                Target Feed
                            </Typography>
                        </Box>
                        <Box sx={{ flexGrow: 1 }}>
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
                            p: 2,
                            borderBottom: `1px solid ${muiTheme.palette.divider}`,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1.5
                        }}>
                            <Typography variant="h6" color="error.main">
                                Threat Log
                            </Typography>
                        </Box>
                        <Box sx={{ p: 2 }}>
                            <AlertQueue alerts={alerts} onAcknowledge={fetchAlerts} />
                        </Box>
                    </Paper>
                </motion.div>
            </Grid>
        </Grid>
    );
};

export default Dashboard;
