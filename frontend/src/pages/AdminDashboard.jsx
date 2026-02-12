import React, { useState, useEffect } from 'react';
import { Box, Typography, Grid, Paper, Tabs, Tab, Button, List, ListItem, Chip, IconButton, useTheme, alpha, Switch, FormControlLabel, TextField, Avatar, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Dialog, DialogTitle, DialogContent, DialogActions, Snackbar, Alert, CircularProgress } from '@mui/material';
import { Shield, Users, Bell, Settings, FileText, CheckCircle, XCircle, UserPlus, Trash2, Camera, AlertCircle, Save, Activity, HardDrive, Cpu, Zap, Lock } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import logoImage from '../assets/logo.png';

const AdminDashboard = () => {
    const theme = useTheme();
    const { operators, addOperator, deleteOperator } = useAuth();
    const [tab, setTab] = useState(0);
    const [alerts, setAlerts] = useState([
        { id: 1, type: 'Aggression', location: 'Gate 4', time: '10:45 AM', operator: 'OP-4921', status: 'Pending' },
        { id: 2, type: 'Loitering', location: 'Parking B', time: '11:02 AM', operator: 'OP-4921', status: 'Pending' },
        { id: 3, type: 'Unauthorized', location: 'Server Room', time: '11:15 AM', operator: 'OP-5502', status: 'Resolved' }
    ]);

    const [auditHistory, setAuditHistory] = useState([]);
    const [loadingLogs, setLoadingLogs] = useState(false);

    const [maintenanceMode, setMaintenanceMode] = useState(false);
    const [systemMetrics, setSystemMetrics] = useState({
        cpu: 42,
        gpu: 68,
        ram: 54,
        latency: 125
    });

    useEffect(() => {
        const interval = setInterval(() => {
            setSystemMetrics(prev => ({
                cpu: Math.min(100, Math.max(0, prev.cpu + (Math.random() * 4 - 2))),
                gpu: Math.min(100, Math.max(0, prev.gpu + (Math.random() * 2 - 1))),
                ram: Math.min(100, Math.max(0, prev.ram + (Math.random() * 0.4 - 0.2))),
                latency: Math.min(500, Math.max(20, prev.latency + Math.floor(Math.random() * 10 - 5)))
            }));
        }, 2000);
        return () => clearInterval(interval);
    }, []);

    const [openAddOp, setOpenAddOp] = useState(false);
    const [newOp, setNewOp] = useState({
        id: `OP-${Math.floor(Math.random() * 9000) + 1000}`,
        name: '',
        shifts: 'Morning',
        securityKey: ''
    });
    const [isExporting, setIsExporting] = useState(false);
    const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
    const [addOpError, setAddOpError] = useState({ name: false, securityKey: false });

    const handleExportReport = () => {
        setIsExporting(true);
        setTimeout(() => {
            setIsExporting(false);
            setNotification({ open: true, message: 'Global Security Report exported successfully!', severity: 'success' });
        }, 2000);
    };

    const handleAddOperator = () => {
        const errors = {
            name: !newOp.name,
            securityKey: !newOp.securityKey
        };
        setAddOpError(errors);

        if (errors.name || errors.securityKey) {
            setNotification({ open: true, message: 'Please fill in all required fields.', severity: 'error' });
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
        setNotification({ open: true, message: 'New operator added to roster.', severity: 'success' });
    };

    const fetchAuditHistory = async () => {
        setLoadingLogs(true);
        try {
            const response = await fetch('http://localhost:8000/alerts/history?limit=50');
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

    const handleAcknowledge = (id) => {
        setAlerts(alerts.map(a => a.id === id ? { ...a, status: 'Acknowledged' } : a));
    };

    const handleResolve = (id) => {
        setAlerts(alerts.map(a => a.id === id ? { ...a, status: 'Resolved' } : a));
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
                                    {new Date(row.resolved_at).toLocaleTimeString()}
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
                    onClick={handleExportReport}
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
                    <Tab icon={<Bell size={18} />} label="Alert Queue" />
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
                                                <AlertCircle size={24} color={alert.status === 'Resolved' ? theme.palette.success.main : theme.palette.error.main} />
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
                                                <Button variant="outlined" color="primary" onClick={() => handleAcknowledge(alert.id)} startIcon={<CheckCircle size={16} />} sx={{ borderRadius: 2, fontWeight: 700 }}>Acknowledge</Button>
                                            )}
                                            {alert.status !== 'Resolved' && (
                                                <Button variant="contained" color="success" onClick={() => handleResolve(alert.id)} sx={{ borderRadius: 2, fontWeight: 700 }}>Resolve</Button>
                                            )}
                                            {alert.status === 'Resolved' && (
                                                <Chip label="Finalized" color="success" sx={{ fontWeight: 800 }} />
                                            )}
                                            <IconButton><XCircle size={20} color={theme.palette.text.secondary} /></IconButton>
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
                                            control={<Switch checked={maintenanceMode} onChange={(e) => setMaintenanceMode(e.target.checked)} color="warning" />}
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

            {/* Notification Snackbar */}
            <Snackbar
                open={notification.open}
                autoHideDuration={4000}
                onClose={() => setNotification({ ...notification, open: false })}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            >
                <Alert severity={notification.severity} sx={{ borderRadius: 3, fontWeight: 700 }}>
                    {notification.message}
                </Alert>
            </Snackbar>
        </Box>
    );
};

export default AdminDashboard;
