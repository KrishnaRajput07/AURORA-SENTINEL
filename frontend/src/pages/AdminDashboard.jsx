import React, { useState } from 'react';
import { Box, Typography, Grid, Paper, Tabs, Tab, Button, List, ListItem, Chip, IconButton, useTheme, alpha, Switch, FormControlLabel, TextField, Avatar } from '@mui/material';
import { Shield, Users, Bell, Settings, FileText, CheckCircle, XCircle, UserPlus, Trash2, Camera, AlertCircle, Save } from 'lucide-react';
import { motion } from 'framer-motion';

const AdminDashboard = () => {
    const theme = useTheme();
    const [tab, setTab] = useState(0);
    const [alerts, setAlerts] = useState([
        { id: 1, type: 'Aggression', location: 'Gate 4', time: '10:45 AM', operator: 'OP-4921', status: 'Pending' },
        { id: 2, type: 'Loitering', location: 'Parking B', time: '11:02 AM', operator: 'OP-4921', status: 'Pending' },
        { id: 3, type: 'Unauthorized', location: 'Server Room', time: '11:15 AM', operator: 'OP-5502', status: 'Resolved' }
    ]);

    const [operators, setOperators] = useState([
        { id: 'OP-4921', name: 'John Doe', status: 'Active', shifts: 'Morning' },
        { id: 'OP-5502', name: 'Sarah Miller', status: 'Active', shifts: 'Evening' }
    ]);

    const handleAcknowledge = (id) => {
        setAlerts(alerts.map(a => a.id === id ? { ...a, status: 'Acknowledged' } : a));
    };

    const handleResolve = (id) => {
        setAlerts(alerts.map(a => a.id === id ? { ...a, status: 'Resolved' } : a));
    };

    return (
        <Box sx={{ pb: 8 }}>
            {/* Header Section */}
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                <Box>
                    <Typography variant="h3" sx={{ fontWeight: 900, letterSpacing: '-0.04em', display: 'flex', alignItems: 'center', gap: 2 }}>
                        Admin <Box sx={{ px: 1.5, py: 0.5, bgcolor: theme.palette.primary.main, color: '#fff', borderRadius: 2, fontSize: '0.9rem', fontWeight: 900 }}>MANAGEMENT</Box>
                    </Typography>
                    <Typography variant="body1" sx={{ color: theme.palette.text.secondary, mt: 1, fontWeight: 500 }}>
                        System-wide oversight, user management, and security configuration.
                    </Typography>
                </Box>
                <Button variant="contained" startIcon={<FileText size={18} />} sx={{ borderRadius: 3, px: 4, py: 1.5, fontWeight: 800 }}>
                    Export Global Report
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
                    <Tab icon={<Bell size={18} />} label="Alert Management" />
                    <Tab icon={<Users size={18} />} label="User Management" />
                    <Tab icon={<Settings size={18} />} label="System Config" />
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
                                <Button variant="contained" startIcon={<UserPlus size={18} />} sx={{ borderRadius: 3 }}>Add New Operator</Button>
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
                                                <IconButton color="error" sx={{ bgcolor: alpha(theme.palette.error.main, 0.05) }}><Trash2 size={20} /></IconButton>
                                            </Box>
                                        </Paper>
                                    </Grid>
                                ))}
                            </Grid>
                        </Box>
                    )}

                    {/* Tab 2: System Config */}
                    {tab === 2 && (
                        <Box sx={{ animation: 'fadeIn 0.4s ease-out' }}>
                            <Typography variant="h6" sx={{ fontWeight: 800, mb: 4 }}>Global Security Parameters</Typography>
                            <Grid container spacing={4}>
                                <Grid item xs={12} md={6}>
                                    <Paper variant="outlined" sx={{ p: 4, borderRadius: 5, display: 'flex', flexDirection: 'column', gap: 4 }}>
                                        <Typography variant="subtitle1" sx={{ fontWeight: 800, borderBottom: `1px solid ${theme.palette.divider}`, pb: 1 }}>Detection Sensitivity</Typography>
                                        <FormControlLabel control={<Switch defaultChecked />} label="Enable Aggression Pose Tracking" />
                                        <FormControlLabel control={<Switch />} label="Strict Crowd Density Alerts" />
                                        <TextField label="Loitering Threshold (seconds)" defaultValue="30" type="number" fullWidth />
                                    </Paper>
                                </Grid>
                                <Grid item xs={12} md={6}>
                                    <Paper variant="outlined" sx={{ p: 4, borderRadius: 5, display: 'flex', flexDirection: 'column', gap: 4 }}>
                                        <Typography variant="subtitle1" sx={{ fontWeight: 800, borderBottom: `1px solid ${theme.palette.divider}`, pb: 1 }}>Infrastructure</Typography>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                            <Camera size={20} />
                                            <Typography variant="body2" sx={{ fontWeight: 600 }}>Main Gate North (ID: CAM-001) - ONLINE</Typography>
                                        </Box>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                            <Camera size={20} />
                                            <Typography variant="body2" sx={{ fontWeight: 600 }}>Lobby Area (ID: CAM-004) - ONLINE</Typography>
                                        </Box>
                                        <Button variant="contained" startIcon={<Save size={18} />} sx={{ mt: 2, borderRadius: 3 }}>Apply All Changes</Button>
                                    </Paper>
                                </Grid>
                            </Grid>
                        </Box>
                    )}
                </Box>
            </Paper>
        </Box>
    );
};

export default AdminDashboard;
