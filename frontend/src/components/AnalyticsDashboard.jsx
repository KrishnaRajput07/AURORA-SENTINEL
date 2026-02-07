import React from 'react';
import { Box, Grid, Typography, Card, CardContent, useTheme, alpha } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid } from 'recharts';
import { Activity, AlertTriangle, ShieldCheck, Siren } from 'lucide-react';

const AnalyticsDashboard = ({ data }) => {
    const theme = useTheme();
    if (!data) return <Typography>Loading Analytics...</Typography>;

    const { total_alerts, critical_alerts, alert_levels } = data;

    const chartData = [
        { name: 'Critical', value: alert_levels?.critical || 0, color: theme.palette.error.main },
        { name: 'High', value: alert_levels?.high || 0, color: theme.palette.warning.main },
        { name: 'Medium', value: alert_levels?.medium || 0, color: theme.palette.info.main },
        { name: 'Safe', value: alert_levels?.low || 0, color: theme.palette.success.main },
    ];

    const StatCard = ({ title, value, icon: Icon, color, bgcolor }) => (
        <Card sx={{
            height: '100%',
            transition: 'transform 0.3s ease-in-out',
            boxShadow: '0 4px 20px rgba(0,0,0,0.03)',
            '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px rgba(0,0,0,0.08)'
            }
        }}>
            <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 3 }}>
                <Box>
                    <Typography color="text.secondary" variant="caption" sx={{ textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                        {title}
                    </Typography>
                    <Typography variant="h3" sx={{ color: theme.palette.text.primary, fontWeight: 700, mt: 1, fontFamily: '"Space Grotesk", sans-serif' }}>
                        {value}
                    </Typography>
                </Box>
                <Box sx={{
                    p: 1.5,
                    borderRadius: '16px',
                    bgcolor: bgcolor || alpha(color, 0.1),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                }}>
                    <Icon color={color} size={28} />
                </Box>
            </CardContent>
        </Card>
    );

    return (
        <Box sx={{ width: '100%' }}>
            <Grid container spacing={3}>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Total Events"
                        value={total_alerts}
                        icon={Activity}
                        color={theme.palette.primary.main}
                        bgcolor="#F0FDF4"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Critical"
                        value={critical_alerts}
                        icon={Siren}
                        color={theme.palette.error.main}
                        bgcolor="#FEF2F2"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Warnings"
                        value={alert_levels?.high || 0}
                        icon={AlertTriangle}
                        color={theme.palette.warning.main}
                        bgcolor="#FFF7ED"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Safe Status"
                        value={alert_levels?.low || 0}
                        icon={ShieldCheck}
                        color={theme.palette.success.main}
                        bgcolor="#F0F9FF"
                    />
                </Grid>

                <Grid item xs={12}>
                    <Card sx={{ p: 0, height: 350, display: 'flex', flexDirection: 'column' }}>
                        <Box sx={{ p: 3, borderBottom: `1px solid ${theme.palette.divider}` }}>
                            <Typography variant="h6" sx={{ fontSize: '1rem', color: theme.palette.text.primary, fontWeight: 600 }}>
                                Threat Distribution
                            </Typography>
                        </Box>
                        <Box sx={{ flexGrow: 1, p: 3 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
                                    <XAxis
                                        dataKey="name"
                                        tick={{ fill: '#64748B', fontSize: 13, fontFamily: 'Inter' }}
                                        axisLine={false}
                                        tickLine={false}
                                        dy={10}
                                    />
                                    <YAxis
                                        tick={{ fill: '#64748B', fontSize: 12, fontFamily: 'Inter' }}
                                        axisLine={false}
                                        tickLine={false}
                                    />
                                    <Tooltip
                                        cursor={{ fill: '#F8FAFC' }}
                                        contentStyle={{
                                            borderRadius: '12px',
                                            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                            border: 'none'
                                        }}
                                    />
                                    <Bar dataKey="value" radius={[6, 6, 0, 0]} barSize={60}>
                                        {chartData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </Box>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
};

export default AnalyticsDashboard;
