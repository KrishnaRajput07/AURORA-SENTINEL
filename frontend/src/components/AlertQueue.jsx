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

const AlertQueue = ({ alerts: propAlerts, onAcknowledge }) => { // propAlerts passed from Dashboard, but we might fetch our own history
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
                body: JSON.stringify({ operator_name: 'Officer DB' }) // Mock operator
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
                    operator_name: 'Officer DB'
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
        <TableContainer sx={{ maxHeight: 440 }}>
            <Table stickyHeader size="small">
                <TableHead>
                    <TableRow>
                        <TableCell sx={{ bgcolor: '#F8FAFC', fontWeight: 600 }}>Time</TableCell>
                        <TableCell sx={{ bgcolor: '#F8FAFC', fontWeight: 600 }}>Level</TableCell>
                        <TableCell sx={{ bgcolor: '#F8FAFC', fontWeight: 600 }}>Camera</TableCell>
                        <TableCell sx={{ bgcolor: '#F8FAFC', fontWeight: 600 }}>Risk</TableCell>
                        <TableCell sx={{ bgcolor: '#F8FAFC', fontWeight: 600 }}>Status</TableCell>
                        {isHistory && <TableCell sx={{ bgcolor: '#F8FAFC', fontWeight: 600 }}>Outcome</TableCell>}
                        <TableCell sx={{ bgcolor: '#F8FAFC', fontWeight: 600 }}>Actions</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    <AnimatePresence>
                        {data.map((alert, index) => (
                            <TableRow
                                key={alert.id}
                                component={motion.tr}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                sx={{
                                    '&:hover': { bgcolor: '#F1F5F9' },
                                    // Pulse animation for pending critical
                                    animation: (alert.status === 'pending' && alert.level === 'CRITICAL') ? 'pulse-red 2s infinite' : 'none',
                                    bgcolor: alert.status === 'pending' && alert.level === 'CRITICAL' ? alpha(theme.palette.error.main, 0.05) : 'inherit'
                                }}
                            >
                                <TableCell>
                                    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                                        <Typography variant="body2" fontWeight={600}>
                                            {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
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
                                            fontWeight: 700,
                                            height: 24,
                                            fontSize: '0.7rem'
                                        }}
                                    />
                                </TableCell>
                                <TableCell>{alert.camera_id}</TableCell>
                                <TableCell>
                                    <Typography fontWeight={700} color={alert.risk_score > 75 ? 'error.main' : 'text.primary'}>
                                        {alert.risk_score.toFixed(0)}%
                                    </Typography>
                                </TableCell>
                                <TableCell>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        {alert.status === 'pending' && <AlertTriangle size={14} color={theme.palette.error.main} />}
                                        {alert.status === 'acknowledged' && <User size={14} color={theme.palette.warning.main} />}
                                        {alert.status === 'resolved' && <CheckCircle size={14} color={theme.palette.success.main} />}
                                        <Typography variant="caption" fontWeight={600} sx={{ textTransform: 'uppercase' }}>
                                            {alert.status}
                                        </Typography>
                                    </Box>
                                    {alert.operator_name && (
                                        <Typography variant="caption" display="block" color="text.secondary">
                                            by {alert.operator_name}
                                        </Typography>
                                    )}
                                </TableCell>

                                {isHistory && (
                                    <TableCell>
                                        <Typography variant="body2">{alert.resolution_type}</Typography>
                                        <Typography variant="caption" color="text.secondary" noWrap sx={{ maxWidth: 150, display: 'block' }}>
                                            {alert.resolution_notes}
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
                                                sx={{ fontSize: '0.7rem', py: 0.5, px: 1.5 }}
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
                                                startIcon={<Shield size={14} />}
                                                sx={{ fontSize: '0.7rem', py: 0.5, px: 2 }}
                                            >
                                                RESOLVE
                                            </Button>
                                        )}
                                        {alert.status === 'resolved' && (
                                            <Button disabled size="small" startIcon={<CheckCircle size={14} />}>Done</Button>
                                        )}
                                    </Box>
                                </TableCell>
                            </TableRow>
                        ))}
                        {data.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={7} sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
                                    No alerts in this queue.
                                </TableCell>
                            </TableRow>
                        )}
                    </AnimatePresence>
                </TableBody>
            </Table>
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
