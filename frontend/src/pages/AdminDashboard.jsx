import React, { useState, useEffect } from 'react';
import { Box, Typography, Grid, Paper, Tabs, Tab, Button, List, ListItem, Chip, IconButton, useTheme, alpha, Switch, FormControlLabel, TextField, Avatar, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Dialog, DialogTitle, DialogContent, DialogActions, Snackbar, Alert, CircularProgress, MenuItem, Slide } from '@mui/material';
import { FileText, Users, Clock, Zap, Settings, Shield, AlertTriangle, Search, Filter, Lock, Plus, MapPin, Eye, Trash2, Check, X, ShieldAlert, UserPlus, Camera, Activity, HardDrive, Cpu, Save, Bell, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useNotifications } from '../context/NotificationContext';
import logoImage from '../assets/logo.png';
import { API_BASE_URL } from '../config';

const Transition = React.forwardRef(function Transition(props, ref) {
    return <Slide direction="up" ref={ref} {...props} />;
});

const RESOLUTION_TYPES = [
    { value: 'Threat Neutralized', label: 'Threat Neutralized', color: 'success' },
    { value: 'False Positive', label: 'False Positive', color: 'info' },
    { value: 'Escalated to Police', label: 'Escalated to Police', color: 'error' },
    { value: 'Situation Resolved', label: 'Situation Resolved', color: 'success' },
    { value: 'Equipment Check', label: 'Equipment Check', color: 'warning' },
];

const AdminDashboard = () => {
    const theme = useTheme();
    const { user, operators, addOperator, deleteOperator } = useAuth();
    const [tab, setTab] = useState(0);
    const [alerts, setAlerts] = useState([]);

    const [auditHistory, setAuditHistory] = useState([]);
    const [loadingLogs, setLoadingLogs] = useState(false);

    const [maintenanceMode, setMaintenanceMode] = useState(false);
    const [systemMetrics, setSystemMetrics] = useState({
        cpu: 42,
        gpu: 68,
        ram: 54,
        latency: 125
    });

    const fetchAlerts = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/alerts/recent`);
            const data = await response.json();
            if (data.alerts) {
                // Map backend fields to frontend names if necessary
                const mappedAlerts = data.alerts.map(a => ({
                    id: a.id,
                    type: a.ai_scene_type ? (a.ai_scene_type.charAt(0).toUpperCase() + a.ai_scene_type.slice(1)) : (a.level || 'Alert'),
                    location: a.location || 'Unknown',
                    time: new Date(a.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    operator: a.operator_name || 'System',
                    status: a.status.charAt(0).toUpperCase() + a.status.slice(1),
                    level: a.level
                }));
                setAlerts(mappedAlerts);
            }
        } catch (error) {
            console.error('Error fetching alerts:', error);
        }
    };

    useEffect(() => {
        const fetchMaintenanceMode = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/settings/maintenance`);
                const data = await response.json();
                setMaintenanceMode(data.maintenance_mode);
            } catch (error) {
                console.error('Error fetching maintenance mode:', error);
            }
        };

        fetchMaintenanceMode();
        fetchAlerts(); // Initial fetch

        const metricsInterval = setInterval(() => {
            setSystemMetrics(prev => ({
                cpu: Math.min(100, Math.max(0, prev.cpu + (Math.random() * 4 - 2))),
                gpu: Math.min(100, Math.max(0, prev.gpu + (Math.random() * 2 - 1))),
                ram: Math.min(100, Math.max(0, prev.ram + (Math.random() * 0.4 - 0.2))),
                latency: Math.min(500, Math.max(20, prev.latency + Math.floor(Math.random() * 10 - 5)))
            }));
        }, 2000);

        const alertsInterval = setInterval(fetchAlerts, 5000); // Polling every 5 seconds for "dynamic" feel

        return () => {
            clearInterval(metricsInterval);
            clearInterval(alertsInterval);
        };
    }, []);

    const toggleMaintenanceMode = async (enabled) => {
        try {
            const response = await fetch(`${API_BASE_URL}/settings/maintenance`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ value: enabled.toString() })
            });
            const data = await response.json();
            setMaintenanceMode(data.maintenance_mode);
            showToast(`Maintenance Mode ${data.maintenance_mode ? 'Activated' : 'Deactivated'}`, data.maintenance_mode ? 'warning' : 'success');
        } catch (error) {
            console.error('Error updating maintenance mode:', error);
            showToast('Failed to update maintenance mode', 'error');
        }
    };

    const { showToast } = useNotifications();
    const [openAddOp, setOpenAddOp] = useState(false);
    const [newOp, setNewOp] = useState({
        id: `OP-${Math.floor(Math.random() * 9000) + 1000}`,
        name: '',
        shifts: 'Morning',
        securityKey: ''
    });
    const [isExporting, setIsExporting] = useState(false);
    const [addOpError, setAddOpError] = useState({ name: false, securityKey: false });

    // Resolve Dialog State
    const [openResolve, setOpenResolve] = useState(false);
    const [selectedAlert, setSelectedAlert] = useState(null);
    const [resolutionType, setResolutionType] = useState('');
    const [resolutionNotes, setResolutionNotes] = useState('');


    const handleAddOperator = () => {
        const errors = {
            name: !newOp.name,
            securityKey: !newOp.securityKey
        };
        setAddOpError(errors);

        if (errors.name || errors.securityKey) {
            showToast('Please fill in all required fields.', 'error');
            return;
        }

        addOperator(newOp);
        setOpenAddOp(false);
        setNewOp({
            id: `OP-${Math.floor(Math.random() * 9000) + 1000}`,
            name: '',
            shifts: 'Morning',
            securityKey: ''
        });
        setAddOpError({ name: false, securityKey: false });
        showToast('New operator added to roster.', 'success');
    };

    const fetchAuditHistory = async () => {
        setLoadingLogs(true);
        try {
            const response = await fetch(`${API_BASE_URL}/alerts/history?limit=50`);
            const data = await response.json();
            setAuditHistory(data.alerts);
        } catch (error) {
            console.error('Error fetching audit history:', error);
        } finally {
            setLoadingLogs(false);
        }
    };

    useEffect(() => {
        if (tab === 2) {
            fetchAuditHistory();
        }
    }, [tab]);

    const handleExportGlobalReport = async () => {
        setIsExporting(true);
        showToast('Generating Global Report...', 'info');
        try {
            // 1. Fetch all data
            const [recentRes, historyRes] = await Promise.all([
                fetch(`${API_BASE_URL}/alerts/recent`),
                fetch(`${API_BASE_URL}/alerts/history`)
            ]);

            const recentData = await recentRes.json();
            const historyData = await historyRes.json();

            const allAlerts = [
                ...(recentData.alerts || []),
                ...(historyData.alerts || [])
            ];

            if (allAlerts.length === 0) {
                showToast('No alerts found to export', 'warning');
                return;
            }

            // 2. Initialize PDF
            const doc = new jsPDF();
            const timestamp = new Date().toLocaleString();

            // 3. Add Header
            doc.setFontSize(22);
            doc.setTextColor(40, 40, 40);
            doc.text("AURORA SENTINEL - GLOBAL SECURITY REPORT", 14, 22);

            doc.setFontSize(10);
            doc.setTextColor(100, 100, 100);
            doc.text(`Generated on: ${timestamp}`, 14, 30);
            doc.text(`System Status: ${maintenanceMode ? 'MAINTENANCE MODE ACTIVE' : 'OPERATIONAL'}`, 14, 35);

            // 4. Add Summary Statistics
            doc.setFontSize(14);
            doc.setTextColor(0, 0, 0);
            doc.text("Summary Statistics", 14, 45);

            const total = allAlerts.length;
            const critical = allAlerts.filter(a => a.level === 'CRITICAL').length;
            const pending = allAlerts.filter(a => a.status === 'pending').length;
            const resolved = allAlerts.filter(a => a.status === 'resolved').length;

            autoTable(doc, {
                startY: 50,
                head: [['Total Alerts', 'Critical Threats', 'Pending Tasks', 'Resolved/Archived']],
                body: [[total, critical, pending, resolved]],
                theme: 'striped',
                headStyles: { fillColor: [44, 62, 80] }
            });

            // 5. Add Detailed Alert Table
            doc.text("Alert Details", 14, doc.lastAutoTable.finalY + 15);

            const tableData = allAlerts.map(a => [
                a.id,
                new Date(a.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }),
                (a.ai_scene_type || a.level).toUpperCase(),
                a.status.toUpperCase(),
                a.operator_name || 'System',
                a.location,
                a.ai_explanation || a.resolution_notes || 'No detailed description available.'
            ]);

            autoTable(doc, {
                startY: doc.lastAutoTable.finalY + 20,
                head: [['ID', 'Timestamp', 'Type', 'Status', 'Operator', 'Location', 'Description Details']],
                body: tableData,
                columnStyles: {
                    6: { cellWidth: 60 } // Description column width
                },
                styles: { fontSize: 8 },
                headStyles: { fillColor: [44, 62, 80] }
            });

            // 6. Save PDF
            doc.save(`Sentinel_Global_Report_${new Date().getTime()}.pdf`);
            showToast('Global Report downloaded successfully', 'success');
            
        } catch (error) {
            console.error('Export Error:', error);
            showToast('Failed to generate report', 'error');
        } finally {
            setIsExporting(false);
        }
    };

    const handleAcknowledge = async (id) => {
        try {
            await fetch(`${API_BASE_URL}/alerts/${id}/acknowledge`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ operator_name: user?.name || 'Admin' })
            });
            fetchAlerts();
            showToast('Alert acknowledged', 'success');
        } catch (error) {
            console.error('Error acknowledging alert:', error);
            showToast('Failed to acknowledge alert', 'error');
        }
    };

    const handleResolve = async (id) => {
        const alert = alerts.find(a => a.id === id);
        if (alert) {
            setSelectedAlert(alert);
            setResolutionType('');
            setResolutionNotes('');
            setOpenResolve(true);
        }
    };

    const submitResolution = async () => {
        if (!selectedAlert || !resolutionType) return;
        try {
            await fetch(`${API_BASE_URL}/alerts/${selectedAlert.id}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    resolution_type: resolutionType,
                    resolution_notes: resolutionNotes || 'Resolved from Admin Dashboard',
                    operator_name: user?.name || 'Admin'
                })
            });
            setOpenResolve(false);
            fetchAlerts();
            fetchAuditHistory(); // Refresh logs immediately
            showToast('Alert resolved and archived', 'success');
        } catch (error) {
            console.error('Error resolving alert:', error);
            showToast('Failed to resolve alert', 'error');
        }
    };

    const AuditLogsTable = () => (
        <Paper variant="outlined" sx={{ width: '100%', overflow: 'hidden', borderRadius: 4 }}>
            <TableContainer>
                <Table size="small">
                    <TableHead sx={{ bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
                        <TableRow>
                            <TableCell sx={{ fontWeight: 800, color: theme.palette.text.primary }}>TIMESTAMP</TableCell>
                            <TableCell sx={{ fontWeight: 800, color: theme.palette.text.primary }}>ACTION</TableCell>
                            <TableCell sx={{ fontWeight: 800, color: theme.palette.text.primary }}>OPERATOR</TableCell>
                            <TableCell sx={{ fontWeight: 800, color: theme.palette.text.primary }}>RESOLUTION / NOTES</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {loadingLogs ? (
                            <TableRow><TableCell colSpan={4} align="center" sx={{ py: 4 }}><Typography variant="body2" color="text.secondary">Fetching secure archives...</Typography></TableCell></TableRow>
                        ) : auditHistory.length === 0 ? (
                            <TableRow><TableCell colSpan={4} align="center" sx={{ py: 4 }}><Typography variant="body2" color="text.secondary">No historical activity recorded yet.</Typography></TableCell></TableRow>
                        ) : auditHistory.map((row, i) => (
                            <TableRow key={i} hover sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                                <TableCell sx={{ fontFamily: 'monospace', fontWeight: 600 }}>
                                    {row.resolved_at ? new Date(row.resolved_at).toLocaleString([], { 
                                        hour: '2-digit', 
                                        minute: '2-digit', 
                                        second: '2-digit',
                                        day: '2-digit',
                                        month: 'short'
                                    }) : 'Unknown'}
                                </TableCell>
                                <TableCell>
                                    <Chip
                                        label="RESOLVED"
                                        size="small"
                                        sx={{
                                            fontWeight: 800,
                                            fontSize: '0.65rem',
                                            bgcolor: alpha(theme.palette.success.main, 0.1),
                                            color: theme.palette.success.main
                                        }}
                                    />
                                </TableCell>
                                <TableCell sx={{ fontWeight: 700 }}>{row.operator_name || 'System'}</TableCell>
                                <TableCell sx={{ color: theme.palette.text.primary, fontWeight: 500 }}>
                                    <Typography variant="body2" component="span" sx={{ color: theme.palette.primary.main, fontWeight: 700 }}>{row.resolution_type}:</Typography> {row.resolution_notes || 'No notes provided'}
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Paper>
    );

    const ResourceMonitor = () => (
        <Grid container spacing={2} sx={{ mb: 4 }}>
            {[
                { label: 'CPU Load', value: `${Math.round(systemMetrics.cpu)}%`, icon: <Cpu />, color: theme.palette.primary.main },
                { label: 'GPU Usage', value: `${Math.round(systemMetrics.gpu)}%`, icon: <Zap />, color: theme.palette.secondary.main },
                { label: 'Memory', value: `${Math.round(systemMetrics.ram)}%`, icon: <HardDrive />, color: '#805AD5' },
                { label: 'Latency', value: `${Math.round(systemMetrics.latency)}ms`, icon: <Activity />, color: theme.palette.error.main },
            ].map((m, i) => (
                <Grid item xs={6} md={3} key={i}>
                    <Paper variant="outlined" sx={{ p: 2, borderRadius: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Box sx={{ p: 1, borderRadius: 2, bgcolor: alpha(m.color, 0.1), color: m.color }}>{m.icon}</Box>
                        <Box>
                            <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 700 }}>{m.label}</Typography>
                            <Typography variant="h6" sx={{ fontWeight: 900, lineHeight: 1 }}>{m.value}</Typography>
                        </Box>
                    </Paper>
                </Grid>
            ))}
        </Grid>
    );

    return (
        <Box sx={{ pb: 8 }}>
            {/* Header Section */}
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2.5 }}>
                    <Box
                        component="img"
                        src={logoImage}
                        sx={{ width: 56, height: 56, objectFit: 'contain', borderRadius: 3, bgcolor: '#fff', p: 0.5, boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }}
                    />
                    <Box>
                        <Typography variant="h3" sx={{ fontWeight: 900, letterSpacing: '-0.04em', display: 'flex', alignItems: 'center', gap: 2 }}>
                            Admin <Box sx={{ px: 1.5, py: 0.5, bgcolor: theme.palette.primary.main, color: '#fff', borderRadius: 2, fontSize: '0.9rem', fontWeight: 900 }}>MANAGEMENT</Box>
                        </Typography>
                        <Typography variant="body1" sx={{ color: theme.palette.text.secondary, mt: 0.5, fontWeight: 500 }}>
                            System-wide oversight, user management, and security configuration.
                        </Typography>
                    </Box>
                </Box>
                <Button
                    variant="contained"
                    startIcon={isExporting ? <CircularProgress size={18} color="inherit" /> : <FileText size={18} />}
                    disabled={isExporting}
                    onClick={handleExportGlobalReport}
                    sx={{ borderRadius: 3, px: 4, py: 1.5, fontWeight: 800 }}
                >
                    {isExporting ? 'Exporting...' : 'Export Global Report'}
                </Button>
            </Box>

            <Paper sx={{ borderRadius: 6, overflow: 'hidden', mb: 4 }}>
                <Tabs
                    value={tab}
                    onChange={(e, v) => setTab(v)}
                    sx={{
                        bgcolor: alpha(theme.palette.primary.main, 0.03),
                        borderBottom: `1px solid ${theme.palette.divider}`,
                        '& .MuiTab-root': { py: 3, fontWeight: 700, textTransform: 'none', fontSize: '1rem', gap: 1 },
                        '& .Mui-selected': { color: theme.palette.primary.main }
                    }}
                >
                    <Tab icon={<AlertTriangle size={18} />} label="Alert Queue" />
                    <Tab icon={<Users size={18} />} label="Operators" />
                    <Tab icon={<FileText size={18} />} label="Audit Logs" />
                    <Tab icon={<Settings size={18} />} label="System Pulse" />
                </Tabs>

                <Box sx={{ p: 4 }}>
                    {/* Tab 0: Alert Management */}
                    {tab === 0 && (
                        <Box sx={{ animation: 'fadeIn 0.4s ease-out' }}>
                            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="h6" sx={{ fontWeight: 800 }}>Master Alert Queue</Typography>
                                <Chip label={`${alerts.filter(a => a.status === 'Pending').length} Pending Tasks`} color="error" sx={{ fontWeight: 800 }} />
                            </Box>
                            <List sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                {alerts.map(alert => (
                                    <Paper key={alert.id} variant="outlined" sx={{ p: 2, borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                                            <Box sx={{ p: 1.5, borderRadius: 3, bgcolor: alert.status === 'Resolved' ? alpha(theme.palette.success.main, 0.1) : alpha(theme.palette.error.main, 0.1) }}>
                                                <AlertTriangle size={24} color={alert.status === 'Resolved' ? theme.palette.success.main : theme.palette.error.main} />
                                            </Box>
                                            <Box>
                                                <Typography variant="subtitle1" sx={{ fontWeight: 800 }}>{alert.type} - {alert.location}</Typography>
                                                <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                                                    Detected at {alert.time} | Logged by <Chip label={alert.operator} size="small" sx={{ height: 20, fontSize: '0.65rem', fontWeight: 700 }} />
                                                </Typography>
                                            </Box>
                                        </Box>
                                        <Box sx={{ display: 'flex', gap: 1.5 }}>
                                            {alert.status === 'Pending' && (
                                                <Button variant="outlined" color="primary" onClick={() => handleAcknowledge(alert.id)} startIcon={<Check size={16} />} sx={{ borderRadius: 2, fontWeight: 700 }}>Acknowledge</Button>
                                            )}
                                            {alert.status !== 'Resolved' && (
                                                <Button variant="contained" color="success" onClick={() => handleResolve(alert.id)} sx={{ borderRadius: 2, fontWeight: 700 }}>Resolve</Button>
                                            )}
                                            {alert.status === 'Resolved' && (
                                                <Chip label="Finalized" color="success" sx={{ fontWeight: 800 }} />
                                            )}
                                            <IconButton><X size={20} color={theme.palette.text.secondary} /></IconButton>
                                        </Box>
                                    </Paper>
                                ))}
                            </List>
                        </Box>
                    )}

                    {/* Tab 1: User Management */}
                    {tab === 1 && (
                        <Box sx={{ animation: 'fadeIn 0.4s ease-out' }}>
                            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="h6" sx={{ fontWeight: 800 }}>Active Personnel</Typography>
                                <Button
                                    variant="contained"
                                    startIcon={<UserPlus size={18} />}
                                    onClick={() => setOpenAddOp(true)}
                                    sx={{ borderRadius: 3 }}
                                >
                                    Add New Operator
                                </Button>
                            </Box>
                            <Grid container spacing={3}>
                                {operators.map(op => (
                                    <Grid item xs={12} md={6} key={op.id}>
                                        <Paper variant="outlined" sx={{ p: 3, borderRadius: 5, display: 'flex', alignItems: 'center', gap: 3 }}>
                                            <Avatar sx={{ width: 56, height: 56, bgcolor: theme.palette.primary.main }}>{op.name.charAt(0)}</Avatar>
                                            <Box sx={{ flexGrow: 1 }}>
                                                <Typography variant="h6" sx={{ fontWeight: 800 }}>{op.name}</Typography>
                                                <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>ID: {op.id} | Shift: {op.shifts}</Typography>
                                            </Box>
                                            <Box>
                                                <IconButton
                                                    color="error"
                                                    sx={{ bgcolor: alpha(theme.palette.error.main, 0.05) }}
                                                    onClick={() => deleteOperator(op.id)}
                                                >
                                                    <Trash2 size={20} />
                                                </IconButton>
                                            </Box>
                                        </Paper>
                                    </Grid>
                                ))}
                            </Grid>
                        </Box>
                    )}

                    {/* Tab 2: Audit Logs */}
                    {tab === 2 && (
                        <Box sx={{ animation: 'fadeIn 0.4s ease-out' }}>
                            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="h6" sx={{ fontWeight: 800 }}>Security Audit History</Typography>
                                <Button size="small" variant="text" sx={{ fontWeight: 700 }}>Clear History</Button>
                            </Box>
                            <AuditLogsTable />
                        </Box>
                    )}

                    {/* Tab 3: System Config / Pulse */}
                    {tab === 3 && (
                        <Box sx={{ animation: 'fadeIn 0.4s ease-out' }}>
                            <Typography variant="h6" sx={{ fontWeight: 800, mb: 3 }}>Real-time System Performance</Typography>
                            <ResourceMonitor />

                            <Typography variant="h6" sx={{ fontWeight: 800, mb: 3 }}>Master Control Panel</Typography>
                            <Grid container spacing={4}>
                                <Grid item xs={12} md={6}>
                                    <Paper variant="outlined" sx={{ p: 4, borderRadius: 5, display: 'flex', flexDirection: 'column', gap: 4 }}>
                                        <Typography variant="subtitle1" sx={{ fontWeight: 800, borderBottom: `1px solid ${theme.palette.divider}`, pb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Lock size={18} /> Master Overrides
                                        </Typography>
                                        <FormControlLabel
                                            control={<Switch checked={maintenanceMode} onChange={(e) => toggleMaintenanceMode(e.target.checked)} color="warning" />}
                                            label={<Box><Typography variant="body1" sx={{ fontWeight: 700 }}>Maintenance Mode</Typography><Typography variant="caption" color="text.secondary">Locks all operator actions and shows maintenance screen</Typography></Box>}
                                        />
                                        <FormControlLabel control={<Switch defaultChecked />} label={<Box><Typography variant="body1" sx={{ fontWeight: 700 }}>Global AI Thresholding</Typography><Typography variant="caption" color="text.secondary">Auto-adjust sensitivity based on system load</Typography></Box>} />
                                    </Paper>
                                </Grid>
                                <Grid item xs={12} md={6}>
                                    <Paper variant="outlined" sx={{ p: 4, borderRadius: 5, display: 'flex', flexDirection: 'column', gap: 4 }}>
                                        <Typography variant="subtitle1" sx={{ fontWeight: 800, borderBottom: `1px solid ${theme.palette.divider}`, pb: 1 }}>Incident Thresholds</Typography>
                                        <TextField label="Loitering Detection (secs)" defaultValue="30" type="number" fullWidth variant="filled" />
                                        <TextField label="Crowd Density (%)" defaultValue="75" type="number" fullWidth variant="filled" />
                                        <Button variant="contained" startIcon={<Save size={18} />} sx={{ mt: 2, borderRadius: 3, py: 1.5, fontWeight: 800 }}>Apply Master Settings</Button>
                                    </Paper>
                                </Grid>
                            </Grid>
                        </Box>
                    )}
                </Box>
            </Paper>


            {/* Resolve Alert Dialog */}
            <Dialog
                open={openResolve}
                onClose={() => setOpenResolve(false)}
                TransitionComponent={Transition}
                fullWidth
                maxWidth="sm"
                PaperProps={{ sx: { borderRadius: 4, p: 1 } }}
            >
                <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1.5, fontWeight: 900 }}>
                    <Shield color={theme.palette.primary.main} />
                    Resolve Alert #{selectedAlert?.id}
                </DialogTitle>
                <DialogContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
                        <Box>
                            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 700, color: theme.palette.text.secondary }}>RESOLUTION OUTCOME</Typography>
                            <TextField
                                select
                                fullWidth
                                value={resolutionType}
                                onChange={(e) => setResolutionType(e.target.value)}
                                variant="outlined"
                                placeholder="Select outcome..."
                            >
                                {RESOLUTION_TYPES.map((option) => (
                                    <MenuItem key={option.value} value={option.value}>
                                        {option.label}
                                    </MenuItem>
                                ))}
                            </TextField>
                        </Box>
                        <Box>
                            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 700, color: theme.palette.text.secondary }}>INCIDENT NOTES</Typography>
                            <TextField
                                fullWidth
                                multiline
                                rows={4}
                                value={resolutionNotes}
                                onChange={(e) => setResolutionNotes(e.target.value)}
                                placeholder="Enter detailed notes about the resolution action taken..."
                                variant="outlined"
                            />
                        </Box>
                    </Box>
                </DialogContent>
                <DialogActions sx={{ px: 3, pb: 2 }}>
                    <Button onClick={() => setOpenResolve(false)} sx={{ fontWeight: 700, color: theme.palette.text.secondary }}>Cancel</Button>
                    <Button 
                        onClick={submitResolution} 
                        variant="contained" 
                        color="success" 
                        disabled={!resolutionType}
                        sx={{ borderRadius: 2, px: 3, fontWeight: 800 }}
                    >
                        Mark Active & Archive
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Add Operator Dialog */}
            <Dialog open={openAddOp} onClose={() => setOpenAddOp(false)} PaperProps={{ sx: { borderRadius: 4, p: 1 } }}>
                <DialogTitle sx={{ fontWeight: 900 }}>Enlist New Personnel</DialogTitle>
                <DialogContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
                        <TextField
                            label="Operator Name"
                            fullWidth
                            autoFocus
                            value={newOp.name}
                            onChange={(e) => {
                                setNewOp({ ...newOp, name: e.target.value });
                                if (e.target.value) setAddOpError(prev => ({ ...prev, name: false }));
                            }}
                            error={addOpError.name}
                            helperText={addOpError.name ? "Name is required" : ""}
                        />
                        <TextField
                            label="Operator ID"
                            fullWidth
                            value={newOp.id}
                            disabled
                        />
                        <TextField
                            label="Security Key"
                            fullWidth
                            type="password"
                            value={newOp.securityKey}
                            onChange={(e) => {
                                setNewOp({ ...newOp, securityKey: e.target.value });
                                if (e.target.value) setAddOpError(prev => ({ ...prev, securityKey: false }));
                            }}
                            error={addOpError.securityKey}
                            helperText={addOpError.securityKey ? "Security Key is required" : ""}
                        />
                        <TextField
                            select
                            label="Shift Assignment"
                            fullWidth
                            SelectProps={{ native: true }}
                            value={newOp.shifts}
                            onChange={(e) => setNewOp({ ...newOp, shifts: e.target.value })}
                        >
                            <option value="Morning">Morning (06:00 - 14:00)</option>
                            <option value="Evening">Evening (14:00 - 22:00)</option>
                            <option value="Night">Night (22:00 - 06:00)</option>
                        </TextField>
                    </Box>
                </DialogContent>
                <DialogActions sx={{ p: 3 }}>
                    <Button onClick={() => setOpenAddOp(false)} color="inherit" sx={{ fontWeight: 700 }}>Cancel</Button>
                    <Button onClick={handleAddOperator} variant="contained" sx={{ fontWeight: 700, borderRadius: 2 }}>Enlist Operator</Button>
                </DialogActions>
            </Dialog>

        </Box>
    );
};

export default AdminDashboard;
