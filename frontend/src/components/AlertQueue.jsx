import React, { useState, useEffect } from 'react';
import {
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
    Chip, Button, Box, Typography, IconButton, useTheme, alpha,
    Tabs, Tab, Dialog, DialogTitle, DialogContent, DialogActions,
    TextField, MenuItem, Slide
} from '@mui/material';
import {
    CheckCircle, Clock, AlertTriangle, Shield, CheckSquare,
    History, User, FileText, X
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Transitions
const Transition = React.forwardRef(function Transition(props, ref) {
    return <Slide direction="up" ref={ref} {...props} />;
});

// Resolution Options
const RESOLUTION_TYPES = [
    { value: 'Threat Neutralized', label: 'Threat Neutralized', color: 'success' },
    { value: 'False Positive', label: 'False Positive', color: 'info' },
    { value: 'Escalated to Police', label: 'Escalated to Police', color: 'error' },
    { value: 'Situation Resolved', label: 'Situation Resolved', color: 'success' },
    { value: 'Equipment Check', label: 'Equipment Check', color: 'warning' },
];

const AlertQueue = ({ alerts: propAlerts, onAcknowledge }) => {
    const { user } = useAuth();
    const theme = useTheme();
    const [activeTab, setActiveTab] = useState(0); // 0: Active, 1: History

    // Local state for full list (merged/managed)
    const [localAlerts, setLocalAlerts] = useState([]);
    const [historyAlerts, setHistoryAlerts] = useState([]);

    // Dialog State
    const [openResolve, setOpenResolve] = useState(false);
    const [selectedAlert, setSelectedAlert] = useState(null);
    const [resolutionType, setResolutionType] = useState('');
    const [resolutionNotes, setResolutionNotes] = useState('');

    // Sync props to local for Active tab (simplified for this demo)
    useEffect(() => {
        if (propAlerts) setLocalAlerts(propAlerts);
    }, [propAlerts]);

    // Fetch history when tab changes
    useEffect(() => {
        if (activeTab === 1) fetchHistory();
    }, [activeTab]);

    const fetchHistory = async () => {
        try {
            const res = await fetch('http://localhost:8000/alerts/history');
            const data = await res.json();
            setHistoryAlerts(data.alerts);
        } catch (e) { console.error(e); }
    };

    const handleAcknowledge = async (alert) => {
        try {
            await fetch(`http://localhost:8000/alerts/${alert.id}/acknowledge`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ operator_name: user?.name || 'Operator' })
            });
            onAcknowledge(); // Refresh parent
        } catch (error) { console.error(error); }
    };

    const openResolutionDialog = (alert) => {
        setSelectedAlert(alert);
        setResolutionType('');
        setResolutionNotes('');
        setOpenResolve(true);
    };

    const submitResolution = async () => {
        if (!selectedAlert || !resolutionType) return;
        try {
            await fetch(`http://localhost:8000/alerts/${selectedAlert.id}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    resolution_type: resolutionType,
                    resolution_notes: resolutionNotes,
                    operator_name: user?.name || 'Operator'
                })
            });
            setOpenResolve(false);
            onAcknowledge(); // Refresh parent (Active list)
            if (activeTab === 1) fetchHistory(); // Refresh history if viewing it
        } catch (error) { console.error(error); }
    };

    const getRiskColor = (level, score) => {
        if (level === 'CRITICAL') return theme.palette.error.main;
        if (level === 'HIGH') return theme.palette.warning.main;
        if (level === 'MEDIUM') return theme.palette.info.main;
        return theme.palette.success.main;
    };

    // Columns config
    const renderTable = (data, isHistory) => (
        <TableContainer sx={{
            maxHeight: 440,
            '&::-webkit-scrollbar': { width: '6px' },
            '&::-webkit-scrollbar-thumb': { bgcolor: alpha(theme.palette.divider, 0.5), borderRadius: '10px' }
        }}>
            <Table stickyHeader size="small">
                <TableHead>
                    <TableRow>
                        {['Time', 'Level', 'Camera', 'Risk', 'Status', ...(isHistory ? ['Outcome'] : []), 'Actions'].map((head) => (
                            <TableCell key={head} sx={{
                                bgcolor: alpha('#FFFFFF', 0.8),
                                backdropFilter: 'blur(8px)',
                                fontWeight: 800,
                                fontSize: '0.75rem',
                                color: theme.palette.text.secondary,
                                borderBottom: `2px solid ${theme.palette.divider}`,
                                py: 2
                            }}>
                                {head.toUpperCase()}
                            </TableCell>
                        ))}
                    </TableRow>
                </TableHead>
                <TableBody>
                    <AnimatePresence mode="popLayout">
                        {data.map((alert, index) => (
                            <TableRow
                                key={alert.id}
                                component={motion.tr}
                                layout
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, scale: 0.95 }}
                                transition={{ duration: 0.2, delay: index * 0.05 }}
                                sx={{
                                    '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.02) },
                                    transition: 'background-color 0.2s ease',
                                    borderBottom: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
                                    // Pulse animation for pending critical
                                    animation: (alert.status === 'pending' && alert.level === 'CRITICAL') ? 'pulse-red 3s infinite' : 'none',
                                    bgcolor: alert.status === 'pending' && alert.level === 'CRITICAL' ? alpha(theme.palette.error.main, 0.02) : 'inherit'
                                }}
                            >
                                <TableCell sx={{ py: 2 }}>
                                    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                                        <Typography variant="body2" sx={{ fontWeight: 700, color: theme.palette.text.primary }}>
                                            {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </Typography>
                                        <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontSize: '0.65rem' }}>
                                            {new Date(alert.timestamp).toLocaleDateString()}
                                        </Typography>
                                    </Box>
                                </TableCell>
                                <TableCell>
                                    <Chip
                                        label={alert.level}
                                        size="small"
                                        sx={{
                                            bgcolor: alpha(getRiskColor(alert.level), 0.1),
                                            color: getRiskColor(alert.level),
                                            fontWeight: 900,
                                            height: 22,
                                            fontSize: '0.65rem',
                                            borderRadius: '6px',
                                            letterSpacing: '0.05em',
                                            border: `1px solid ${alpha(getRiskColor(alert.level), 0.2)}`
                                        }}
                                    />
                                </TableCell>
                                <TableCell sx={{ fontWeight: 600, color: theme.palette.text.secondary }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        {alert.camera_id}
                                        {alert.camera_id === 'FORENSIC-01' && (
                                            <Chip
                                                label="FORENSIC"
                                                size="small"
                                                variant="outlined"
                                                sx={{
                                                    height: 18,
                                                    fontSize: '0.6rem',
                                                    fontWeight: 900,
                                                    borderColor: theme.palette.primary.main,
                                                    color: theme.palette.primary.main
                                                }}
                                            />
                                        )}
                                    </Box>
                                </TableCell>
                                <TableCell>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <Box sx={{
                                            width: 4,
                                            height: 20,
                                            borderRadius: 1,
                                            bgcolor: getRiskColor(alert.level)
                                        }} />
                                        <Typography sx={{ fontWeight: 900, color: theme.palette.text.primary, fontSize: '0.9rem', fontFamily: 'monospace' }}>
                                            {alert.risk_score.toFixed(0)}%
                                        </Typography>
                                    </Box>
                                </TableCell>
                                <TableCell>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <Box sx={{
                                            p: 0.5,
                                            bgcolor: alert.status === 'pending' ? alpha(theme.palette.error.main, 0.1) :
                                                alert.status === 'acknowledged' ? alpha(theme.palette.warning.main, 0.1) :
                                                    alpha(theme.palette.success.main, 0.1),
                                            borderRadius: '50%',
                                            display: 'flex'
                                        }}>
                                            {alert.status === 'pending' && <AlertTriangle size={12} color={theme.palette.error.main} />}
                                            {alert.status === 'acknowledged' && <User size={12} color={theme.palette.warning.main} />}
                                            {alert.status === 'resolved' && <CheckCircle size={12} color={theme.palette.success.main} />}
                                        </Box>
                                        <Typography variant="caption" sx={{ fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '0.65rem' }}>
                                            {alert.status}
                                        </Typography>
                                    </Box>
                                </TableCell>

                                {isHistory && (
                                    <TableCell>
                                        <Typography variant="body2" sx={{ fontWeight: 600 }}>{alert.resolution_type}</Typography>
                                        <Typography variant="caption" color="text.secondary" noWrap sx={{ maxWidth: 150, display: 'block', fontStyle: 'italic' }}>
                                            "{alert.resolution_notes}"
                                        </Typography>
                                    </TableCell>
                                )}

                                <TableCell>
                                    <Box sx={{ display: 'flex', gap: 1 }}>
                                        {alert.status === 'pending' && (
                                            <Button
                                                variant="contained"
                                                size="small"
                                                color="warning"
                                                onClick={() => handleAcknowledge(alert)}
                                                startIcon={<CheckSquare size={14} />}
                                                sx={{
                                                    fontSize: '0.65rem',
                                                    fontWeight: 800,
                                                    borderRadius: '6px',
                                                    boxShadow: 'none',
                                                    '&:hover': { boxShadow: `0 4px 12px ${alpha(theme.palette.warning.main, 0.3)}` }
                                                }}
                                            >
                                                ACK
                                            </Button>
                                        )}
                                        {alert.status !== 'resolved' && (
                                            <Button
                                                variant="outlined"
                                                size="small"
                                                color="success"
                                                onClick={() => openResolutionDialog(alert)}
                                                sx={{
                                                    fontSize: '0.65rem',
                                                    fontWeight: 800,
                                                    borderRadius: '6px',
                                                    borderWidth: '2px',
                                                    '&:hover': { borderWidth: '2px' }
                                                }}
                                            >
                                                RESOLVE
                                            </Button>
                                        )}
                                        {alert.status === 'resolved' && (
                                            <Chip label="ARCHIVED" size="small" variant="outlined" sx={{ fontSize: '0.6rem', fontWeight: 800 }} />
                                        )}
                                    </Box>
                                </TableCell>
                            </TableRow>
                        ))}
                    </AnimatePresence>
                </TableBody>
            </Table>
            {data.length === 0 && (
                <Box sx={{ textAlign: 'center', py: 8, opacity: 0.5 }}>
                    <Shield size={48} color={theme.palette.divider} style={{ marginBottom: 16 }} />
                    <Typography variant="body1" fontWeight={700}>System Clear</Typography>
                    <Typography variant="caption">No active threats detected in this queue.</Typography>
                </Box>
            )}
        </TableContainer>
    );

    return (
        <React.Fragment>
            <Box sx={{ width: '100%' }}>
                <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 0 }}>
                    <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)}>
                        <Tab label={`Active Queue (${localAlerts.length})`} icon={<AlertTriangle size={16} />} iconPosition="start" />
                        <Tab label="Historical Archive" icon={<History size={16} />} iconPosition="start" />
                    </Tabs>
                </Box>
                <Box sx={{ p: 0 }}>
                    {activeTab === 0 ? renderTable(localAlerts, false) : renderTable(historyAlerts, true)}
                </Box>
            </Box>

            {/* Resolution Dialog */}
            <Dialog
                open={openResolve}
                onClose={() => setOpenResolve(false)}
                TransitionComponent={Transition}
                fullWidth
                maxWidth="sm"
            >
                <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1, bgcolor: '#F8FAFC', borderBottom: `1px solid ${theme.palette.divider}` }}>
                    <Shield color={theme.palette.primary.main} />
                    Resolve Alert #{selectedAlert?.id}
                </DialogTitle>
                <DialogContent sx={{ mt: 2 }}>
                    <Box sx={{ my: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>Resolution Outcome</Typography>
                        <TextField
                            select
                            fullWidth
                            value={resolutionType}
                            onChange={(e) => setResolutionType(e.target.value)}
                            size="small"
                        >
                            {RESOLUTION_TYPES.map((option) => (
                                <MenuItem key={option.value} value={option.value}>
                                    {option.label}
                                </MenuItem>
                            ))}
                        </TextField>
                    </Box>
                    <Box sx={{ my: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>Incident Notes</Typography>
                        <TextField
                            fullWidth
                            multiline
                            rows={3}
                            value={resolutionNotes}
                            onChange={(e) => setResolutionNotes(e.target.value)}
                            placeholder="Enter details about the resolution..."
                            size="small"
                        />
                    </Box>
                </DialogContent>
                <DialogActions sx={{ p: 2, borderTop: `1px solid ${theme.palette.divider}` }}>
                    <Button onClick={() => setOpenResolve(false)} color="inherit">Cancel</Button>
                    <Button
                        onClick={submitResolution}
                        variant="contained"
                        color="success"
                        disabled={!resolutionType}
                    >
                        Mark Active & Archive
                    </Button>
                </DialogActions>
            </Dialog>

            <style>
                {`
                @keyframes pulse-red {
                    0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.4); }
                    70% { box-shadow: 0 0 0 6px rgba(220, 38, 38, 0); }
                    100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
                }
                `}
            </style>
        </React.Fragment>
    );
};

export default AlertQueue;
