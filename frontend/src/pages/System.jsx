import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Grid, Switch, FormControlLabel, Divider, useTheme, Tabs, Tab, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, Button } from '@mui/material';
import { Server, Database, Shield, Cpu, Activity, Users, FileText, HardDrive, RefreshCw } from 'lucide-react';

const SystemPage = () => {
    const [tabIndex, setTabIndex] = useState(0);
    const [health, setHealth] = useState(null);
    const theme = useTheme();

    useEffect(() => {
        fetch('http://localhost:8001/health')
            .then(res => res.json())
            .then(data => setHealth(data))
            .catch(err => console.error(err));
    }, []);

    const handleTabChange = (event, newValue) => {
        setTabIndex(newValue);
    };

    // --- Sub-Components ---

    const GeneralTab = () => (
        <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
                <Paper sx={{ p: 0, borderRadius: 2, border: '1px solid #E2E8F0', overflow: 'hidden' }}>
                    <Box sx={{ px: 2, py: 1.5, bgcolor: '#F7FAFC', borderBottom: '1px solid #E2E8F0' }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#4A5568' }}>SERVICE STATUS</Typography>
                    </Box>
                    <Box sx={{ p: 2 }}>
                        <Grid container spacing={2}>
                            <StatusRow icon={<Server size={18} />} label="API Gateway" value={health?.status === 'healthy' ? 'ONLINE' : 'DOWN'} status={health?.status === 'healthy' ? 'success' : 'error'} />
                            <StatusRow icon={<Database size={18} />} label="PostgreSQL DB" value={health?.database || 'CONNECTING'} status={health?.database === 'connected' ? 'success' : 'warning'} />
                            <StatusRow icon={<Cpu size={18} />} label="Inference Engine" value={health?.gpu_available ? 'GPU ACCEL' : 'CPU MODE'} status="info" />
                            <StatusRow icon={<HardDrive size={18} />} label="Storage" value="45% USED" status="success" />
                        </Grid>
                    </Box>
                </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
                <Paper sx={{ p: 0, borderRadius: 2, border: '1px solid #E2E8F0', overflow: 'hidden' }}>
                    <Box sx={{ px: 2, py: 1.5, bgcolor: '#F7FAFC', borderBottom: '1px solid #E2E8F0' }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#4A5568' }}>LOCAL CONFIGURATION</Typography>
                    </Box>
                    <Box sx={{ p: 3 }}>
                        <FormControlLabel control={<Switch defaultChecked size="small" />} label={<Typography variant="body2">Enable Audio Alerts</Typography>} sx={{ mb: 1, display: 'flex' }} />
                        <FormControlLabel control={<Switch defaultChecked size="small" />} label={<Typography variant="body2">Auto-Archive Events</Typography>} sx={{ mb: 1, display: 'flex' }} />
                        <FormControlLabel control={<Switch size="small" />} label={<Typography variant="body2">Developer/Debug Mode</Typography>} sx={{ mb: 1, display: 'flex' }} />
                        <Divider sx={{ my: 2 }} />
                        <Button variant="outlined" size="small" startIcon={<RefreshCw size={14} />}>Recalibrate Sensors</Button>
                    </Box>
                </Paper>
            </Grid>
        </Grid>
    );

    const AccessControlTab = () => (
        <Paper sx={{ width: '100%', overflow: 'hidden', borderRadius: 2, border: '1px solid #E2E8F0' }}>
            <TableContainer>
                <Table size="small">
                    <TableHead sx={{ bgcolor: '#F7FAFC' }}>
                        <TableRow>
                            <TableCell sx={{ fontWeight: 600, color: '#718096' }}>USER</TableCell>
                            <TableCell sx={{ fontWeight: 600, color: '#718096' }}>ROLE</TableCell>
                            <TableCell sx={{ fontWeight: 600, color: '#718096' }}>LAST ACTIVE</TableCell>
                            <TableCell sx={{ fontWeight: 600, color: '#718096' }}>STATUS</TableCell>
                            <TableCell align="right" sx={{ fontWeight: 600, color: '#718096' }}>ACTIONS</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {[
                            { user: 'admin@sentinel.ai', role: 'Administrator', active: 'Now', status: 'Active' },
                            { user: 'operator_01', role: 'Operator', active: '2m ago', status: 'Active' },
                            { user: 'viewer_guest', role: 'Viewer', active: '5h ago', status: 'Inactive' },
                        ].map((row) => (
                            <TableRow key={row.user} hover>
                                <TableCell sx={{ fontWeight: 500 }}>{row.user}</TableCell>
                                <TableCell><Chip label={row.role} size="small" variant="outlined" /></TableCell>
                                <TableCell>{row.active}</TableCell>
                                <TableCell>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: row.status === 'Active' ? 'success.main' : 'text.disabled' }} />
                                        {row.status}
                                    </Box>
                                </TableCell>
                                <TableCell align="right">
                                    <Button size="small" sx={{ minWidth: 'auto' }}>Edit</Button>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Paper>
    );

    const AuditLogsTab = () => (
        <Paper sx={{ width: '100%', overflow: 'hidden', borderRadius: 2, border: '1px solid #E2E8F0' }}>
            <TableContainer>
                <Table size="small">
                    <TableHead sx={{ bgcolor: '#F7FAFC' }}>
                        <TableRow>
                            <TableCell sx={{ fontWeight: 600, color: '#718096' }}>TIMESTAMP</TableCell>
                            <TableCell sx={{ fontWeight: 600, color: '#718096' }}>ACTION</TableCell>
                            <TableCell sx={{ fontWeight: 600, color: '#718096' }}>USER</TableCell>
                            <TableCell sx={{ fontWeight: 600, color: '#718096' }}>DETAILS</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {[
                            { time: '10:42:05', action: 'LOGIN_SUCCESS', user: 'operator_01', details: 'IP: 192.168.1.105' },
                            { time: '10:15:30', action: 'CONFIG_UPDATE', user: 'admin', details: 'Threshold set to 0.75' },
                            { time: '09:55:12', action: 'ALERT_ACK', user: 'operator_01', details: 'ID: ALERT-9932' },
                            { time: '09:00:01', action: 'SYSTEM_START', user: 'system', details: 'Service initialization' },
                        ].map((row, i) => (
                            <TableRow key={i} hover>
                                <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{row.time}</TableCell>
                                <TableCell sx={{ fontWeight: 600, color: theme.palette.primary.main }}>{row.action}</TableCell>
                                <TableCell>{row.user}</TableCell>
                                <TableCell sx={{ color: 'text.secondary' }}>{row.details}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Paper>
    );

    return (
        <Box>
            <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                    <Typography variant="h5" sx={{ fontWeight: 700, color: '#1A202C', letterSpacing: '-0.02em' }}>
                        System Management
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        Configure system parameters, manage users, and view audit logs.
                    </Typography>
                </Box>
                <Button variant="contained" startIcon={<Shield size={18} />} disableElevation>
                    Security Check
                </Button>
            </Box>

            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
                <Tabs value={tabIndex} onChange={handleTabChange} textColor="primary" indicatorColor="primary">
                    <Tab label="General" icon={<Activity size={16} />} iconPosition="start" sx={{ minHeight: 48 }} />
                    <Tab label="Access Control" icon={<Users size={16} />} iconPosition="start" sx={{ minHeight: 48 }} />
                    <Tab label="Audit Logs" icon={<FileText size={16} />} iconPosition="start" sx={{ minHeight: 48 }} />
                </Tabs>
            </Box>

            {tabIndex === 0 && <GeneralTab />}
            {tabIndex === 1 && <AccessControlTab />}
            {tabIndex === 2 && <AuditLogsTab />}
        </Box>
    );
};

const StatusRow = ({ icon, label, value, status }) => (
    <Grid item xs={12}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 1, borderRadius: 1, '&:hover': { bgcolor: '#F7FAFC' } }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ color: '#718096' }}>{icon}</Box>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{label}</Typography>
            </Box>
            <Chip
                label={value}
                size="small"
                color={status === 'error' ? 'error' : status === 'warning' ? 'warning' : status === 'success' ? 'success' : 'default'}
                variant={status === 'info' ? 'outlined' : 'filled'}
                sx={{ height: 24, borderRadius: '6px', fontWeight: 600, fontSize: '0.75rem' }}
            />
        </Box>
    </Grid>
);

export default SystemPage;
