import React, { useState, useEffect } from 'react';
import { Grid, Typography, Paper, Box, useTheme, Chip, IconButton } from '@mui/material';
import RiskHeatmap from '../components/RiskHeatmap';
import AlertQueue from '../components/AlertQueue';
import LiveFeed from '../components/LiveFeed';
import AnalyticsDashboard from '../components/AnalyticsDashboard';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Shield, AlertTriangle, MoreHorizontal } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNotifications } from '../context/NotificationContext';
import { API_BASE_URL } from '../config';

const Dashboard = () => {
    const { user } = useAuth();
    const { addNotification } = useNotifications();
    const [alerts, setAlerts] = useState([]);
    const [riskData, setRiskData] = useState(null);
    const theme = useTheme();

    useEffect(() => {
        if (riskData?.risk_level && parseFloat(riskData.risk_level) > 30) {
            addNotification({
                title: `Elevated Threat: ${riskData.risk_level}%`,
                level: 'Warning'
            });
        }
    }, [riskData, addNotification]);

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
            const response = await fetch(`${API_BASE_URL}/alerts/recent`);
            const data = await response.json();
            setAlerts(data.alerts);
        } catch (error) { console.error('Error fetching alerts:', error); }
    };

    const fetchRiskData = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/analytics/dashboard`);
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
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                        <TypewriterHeader name={user?.name} />
                        <CyberID id={user?.id || 'OP-4921'} role={user?.role} />
                    </Box>
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
                        height: 400,
                        display: 'flex',
                        flexDirection: 'column',
                        overflow: 'hidden'
                    }}>
                        {/* Clean Header */}
                        <Box sx={{
                            py: 2,
                            px: 3,
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
                    <Paper sx={{ p: 0, height: 400, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                        <Box sx={{
                            py: 1,
                            px: 2.5,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1.25,
                        }}>
                            <Box sx={{ p: 0.75, bgcolor: '#FFF7ED', borderRadius: '50%' }}> {/* Soft orange bg */}
                                <Shield size={16} color={theme.palette.secondary.main} />
                            </Box>
                            <Typography variant="h6" sx={{ fontSize: '0.9rem', color: theme.palette.text.primary, fontWeight: 700 }}>
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

const TypewriterHeader = ({ name }) => {
    const greetings = ["Hello", "Namaste", "Hola", "Bonjour", "Ciao"];
    const [text, setText] = useState("");
    const [isDeleting, setIsDeleting] = useState(false);
    const [phraseIndex, setPhraseIndex] = useState(0);
    const [typingSpeed, setTypingSpeed] = useState(100);

    useEffect(() => {
        const currentPhrase = `${greetings[phraseIndex]} ${name || 'Operator'}`;

        const handleTyping = () => {
            if (!isDeleting && text === currentPhrase) {
                setTimeout(() => setIsDeleting(true), 1500); // Pause at end
                return;
            }
            if (isDeleting && text === "") {
                setIsDeleting(false);
                setPhraseIndex((prev) => (prev + 1) % greetings.length);
                return;
            }

            const nextText = isDeleting
                ? currentPhrase.substring(0, text.length - 1)
                : currentPhrase.substring(0, text.length + 1);

            setText(nextText);
            setTypingSpeed(isDeleting ? 50 : 100);
        };

        const timer = setTimeout(handleTyping, typingSpeed);
        return () => clearTimeout(timer);
    }, [text, isDeleting, phraseIndex, typingSpeed, greetings, name]);

    return (
        <Typography variant="h4" sx={{
            fontWeight: 800,
            color: 'text.primary',
            letterSpacing: '-0.02em',
            display: 'flex',
            alignItems: 'center',
            minHeight: '1.2em'
        }}>
            {text}
            <motion.span
                animate={{ opacity: [1, 0] }}
                transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
                style={{
                    display: 'inline-block',
                    width: '3px',
                    height: '1em',
                    backgroundColor: '#10b981',
                    marginLeft: '4px'
                }}
            />
        </Typography>
    );
};

const CyberID = ({ id, role }) => {
    const theme = useTheme();
    return (
        <Box sx={{
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
            px: 2,
            py: 0.75,
            background: 'rgba(16, 185, 129, 0.05)',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            borderRadius: '8px',
            overflow: 'hidden',
            '&::after': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.05), transparent)',
                transform: 'translateX(-100%)',
                animation: 'shimmer 3s infinite'
            },
            '@keyframes shimmer': {
                '100%': { transform: 'translateX(100%)' }
            }
        }}>
            <Box sx={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                bgcolor: '#10b981',
                boxShadow: '0 0 8px #10b981',
                animation: 'pulse 2s infinite'
            }} />
            <Typography sx={{
                fontFamily: 'monospace',
                fontSize: '0.8rem',
                fontWeight: 700,
                color: '#10b981',
                letterSpacing: '0.1em'
            }}>
                ID: {id}
            </Typography>
            <Box sx={{ height: '12px', width: '1px', bgcolor: 'rgba(16, 185, 129, 0.2)' }} />
            <Typography sx={{
                fontSize: '0.7rem',
                fontWeight: 800,
                color: 'text.secondary',
                textTransform: 'uppercase'
            }}>
                SECURE ACCESS
            </Typography>
        </Box>
    );
};

export default Dashboard;
