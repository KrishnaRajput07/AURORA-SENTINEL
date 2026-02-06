import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Grid, Switch, FormControlLabel, Divider, useTheme } from '@mui/material';
import { Server, Database, Shield, Cpu, Activity } from 'lucide-react';

const SystemPage = () => {
    const [health, setHealth] = useState(null);
    const theme = useTheme(); // Access theme for colors

    useEffect(() => {
        fetch('http://localhost:8000/health')
            .then(res => res.json())
            .then(data => setHealth(data))
            .catch(err => console.error(err));
    }, []);

    const StatusItem = ({ icon, label, value, status }) => (
        <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between', bgcolor: 'background.paper' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                {icon}
                <Typography variant="body1">{label}</Typography>
            </Box>
            <Box sx={{ textAlign: 'right' }}>
                <Typography variant="subtitle2" color={status === 'success' ? 'success.main' : 'warning.main'}>
                    {value}
                </Typography>
            </Box>
        </Paper>
    );

    return (
        <Box>
            <Typography variant="h5" color="text.primary" sx={{ mb: 3, letterSpacing: '0.05em' }}>
                SYSTEM CONFIGURATION
            </Typography>

            <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                    <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>SYSTEM STATUS</Typography>
                    <Grid container spacing={2}>
                        <Grid item xs={12}>
                            <StatusItem
                                icon={<Server color={theme.palette.info.main} />}
                                label="API Server"
                                value={health?.status === 'healthy' ? 'ONLINE' : 'OFFLINE'}
                                status={health?.status === 'healthy' ? 'success' : 'error'}
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <StatusItem
                                icon={<Database color={theme.palette.secondary.main} />}
                                label="Database Connection"
                                value={health?.database || 'Checking...'}
                                status={health?.database === 'connected' ? 'success' : 'error'}
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <StatusItem
                                icon={<Cpu color={theme.palette.success.main} />}
                                label="AI Engine GPU"
                                value={health?.gpu_available ? 'ACTIVE' : 'INACTIVE (CPU MODE)'}
                                status={health?.gpu_available ? 'success' : 'warning'}
                            />
                        </Grid>
                    </Grid>
                </Grid>

                <Grid item xs={12} md={6}>
                    <Typography variant="h6" sx={{ mb: 2, color: 'secondary.main' }}>PREFERENCES (LOCAL)</Typography>
                    <Paper sx={{ p: 3, bgcolor: 'rgba(255,255,255,0.03)' }}>
                        <FormControlLabel control={<Switch defaultChecked />} label="Enable Audio Alerts" sx={{ display: 'block', mb: 2 }} />
                        <Divider sx={{ my: 1, borderColor: 'rgba(255,255,255,0.1)' }} />
                        <FormControlLabel control={<Switch defaultChecked />} label="Auto-Connect Live Feed" sx={{ display: 'block', mb: 2 }} />
                        <Divider sx={{ my: 1, borderColor: 'rgba(255,255,255,0.1)' }} />
                        <FormControlLabel control={<Switch />} label="Debug Mode (Show Bounding Boxes)" sx={{ display: 'block', mb: 2 }} />
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};

export default SystemPage;
