import React, { useState, useEffect } from 'react';
import { Grid, Typography, Paper, Box, useTheme, Chip, IconButton } from '@mui/material';
import RiskHeatmap from '../components/RiskHeatmap';
import AlertQueue from '../components/AlertQueue';
import LiveFeed from '../components/LiveFeed';
import AnalyticsDashboard from '../components/AnalyticsDashboard';
import { motion } from 'framer-motion';
import LayoutGrid from '../components/LayoutGrid';
import { Activity, Shield, AlertTriangle, MoreHorizontal } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNotifications } from '../context/NotificationContext';
import { API_BASE_URL } from '../config';

const GREETINGS = ["Hello", "Namaste", "Hola", "Bonjour", "Ciao"];

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

    return (
        <Grid container spacing={4}>
            {/* Header Area */}
            <Grid item xs={12}>
                <Box sx={{ mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                        <TypewriterHeader name={user?.name} />
                        <CyberID id={user?.id || 'OP-4921'} />
                    </Box>
                    <Typography variant="body1" sx={{ color: theme.palette.text.secondary }}>
                        Live monitoring and safety analytics.
                    </Typography>
                </Box>
            </Grid>

            {/* Animated Aceternity Layout Grid */}
            <Grid item xs={12}>
                <LayoutGrid 
                    columns={3}
                    cards={[
                        {
                            id: 'heatmap',
                            colSpan: { xs: 'span 1', md: 'span 2' },
                            content: (
                                <Paper sx={{ p: 0, height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden', pointerEvents: 'auto' }}>
                                    <Box sx={{ py: 3, px: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                            <Box sx={{ p: 1.5, bgcolor: '#F0FDF4', borderRadius: '50%' }}>
                                                <Activity size={28} color={theme.palette.primary.main} />
                                            </Box>
                                            <Typography variant="h6" sx={{ fontSize: '1.2rem', color: theme.palette.text.primary, fontWeight: 700 }}>
                                                Live Activity Map
                                            </Typography>
                                        </Box>
                                        <Chip label="Active" size="small" color="success" sx={{ height: 32, fontSize: '0.9rem' }} />
                                    </Box>
                                    <Box sx={{ flexGrow: 1, position: 'relative' }}>
                                        <RiskHeatmap alerts={alerts} />
                                    </Box>
                                </Paper>
                            )
                        },
                        {
                            id: 'camera',
                            isMaximizable: true,
                            colSpan: { xs: 'span 1', md: 'span 1' },
                            content: ({ isSelected }) => (
                                <Paper sx={{ p: 0, height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden', pointerEvents: 'auto' }}>
                                    <Box sx={{ py: 1, px: 2.5, display: 'flex', alignItems: 'center', gap: 1.25 }}>
                                        <Box sx={{ p: 0.75, bgcolor: '#FFF7ED', borderRadius: '50%' }}>
                                            <Shield size={16} color={theme.palette.secondary.main} />
                                        </Box>
                                        <Typography variant="h6" sx={{ fontSize: '0.9rem', color: theme.palette.text.primary, fontWeight: 700 }}>
                                            Camera Feed
                                        </Typography>
                                    </Box>
                                    <Box sx={{ flexGrow: 1, bgcolor: '#000', position: 'relative' }}>
                                        <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}>
                                            <LiveFeed isExpanded={isSelected} />
                                        </Box>
                                    </Box>
                                </Paper>
                            )
                        },
                        {
                            id: 'analytics',
                            colSpan: { xs: 'span 1', md: 'span 3' },
                            content: (
                                <Box sx={{ height: '100%', pointerEvents: 'auto' }}>
                                    <AnalyticsDashboard data={riskData} />
                                </Box>
                            )
                        },
                        {
                            id: 'alerts',
                            colSpan: { xs: 'span 1', md: 'span 3' },
                            content: (
                                <Paper sx={{ p: 0, height: '100%', overflow: 'hidden', pointerEvents: 'auto', display: 'flex', flexDirection: 'column' }}>
                                    <Box sx={{ p: 3, borderBottom: `1px solid ${theme.palette.divider}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                                            <Box sx={{ p: 1, bgcolor: '#FEF2F2', borderRadius: '50%' }}>
                                                <AlertTriangle size={20} color={theme.palette.error.main} />
                                            </Box>
                                            <Typography variant="h6" sx={{ fontSize: '1rem', color: theme.palette.text.primary, fontWeight: 700 }}>
                                                Recent Alerts
                                            </Typography>
                                        </Box>
                                        <IconButton size="small"><MoreHorizontal size={20} /></IconButton>
                                    </Box>
                                    <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
                                        <AlertQueue alerts={alerts} onAcknowledge={fetchAlerts} />
                                    </Box>
                                </Paper>
                            )
                        }
                    ]} 
                />
            </Grid>
        </Grid>
    );
};

const TypewriterHeader = ({ name }) => {
    const [text, setText] = useState("");
    const [isDeleting, setIsDeleting] = useState(false);
    const [phraseIndex, setPhraseIndex] = useState(0);
    const [typingSpeed, setTypingSpeed] = useState(100);

    useEffect(() => {
        const currentPhrase = `${GREETINGS[phraseIndex]} ${name || 'Operator'}`;

        const handleTyping = () => {
            if (!isDeleting && text === currentPhrase) {
                setTimeout(() => setIsDeleting(true), 1500); // Pause at end
                return;
            }
            if (isDeleting && text === "") {
                setIsDeleting(false);
                setPhraseIndex((prev) => (prev + 1) % GREETINGS.length);
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
    }, [text, isDeleting, phraseIndex, typingSpeed, name]);

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

const CyberID = ({ id }) => {
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
