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
            position: 'relative',
            overflow: 'hidden',
            transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
            border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
            boxShadow: `0 4px 12px ${alpha(color, 0.05)}`,
            '&:hover': {
                transform: 'translateY(-6px)',
                boxShadow: `0 12px 24px ${alpha(color, 0.15)}`,
                '& .icon-container': { transform: 'scale(1.1) rotate(5deg)' }
            }
        }}>
            {/* Glossy Background Accent */}
            <Box sx={{
                position: 'absolute',
                top: -20,
                right: -20,
                width: 100,
                height: 100,
                borderRadius: '50%',
                background: `radial-gradient(circle, ${alpha(color, 0.15)} 0%, transparent 70%)`,
                zIndex: 0
            }} />

            <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 3, position: 'relative', zIndex: 1 }}>
                <Box>
                    <Typography color="text.secondary" variant="caption" sx={{
                        textTransform: 'uppercase',
                        letterSpacing: '0.15em',
                        fontWeight: 800,
                        fontSize: '0.65rem',
                        opacity: 0.8
                    }}>
                        {title}
                    </Typography>
                    <Typography variant="h3" sx={{
                        color: theme.palette.text.primary,
                        fontWeight: 900,
                        mt: 0.5,
                        fontFamily: '"Space Grotesk", monospace',
                        letterSpacing: '-0.02em'
                    }}>
                        {value}
                    </Typography>
                </Box>
                <Box className="icon-container" sx={{
                    p: 1.5,
                    borderRadius: '12px',
                    bgcolor: bgcolor || alpha(color, 0.1),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'transform 0.4s ease',
                    boxShadow: `0 4px 12px ${alpha(color, 0.2)}`
                }}>
                    <Icon color={color} size={24} strokeWidth={2.5} />
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
                        color="#6366F1" // Indigo
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Critical"
                        value={critical_alerts}
                        icon={Siren}
                        color="#EF4444" // Red
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Warnings"
                        value={alert_levels?.high || 0}
                        icon={AlertTriangle}
                        color="#F59E0B" // Amber
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Safe Status"
                        value={alert_levels?.low || 0}
                        icon={ShieldCheck}
                        color="#10B981" // Emerald
                    />
                </Grid>

                <Grid item xs={12}>
                    <Card sx={{
                        p: 0,
                        height: 380,
                        display: 'flex',
                        flexDirection: 'column',
                        borderRadius: 3,
                        border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
                        boxShadow: '0 4px 20px rgba(0,0,0,0.03)'
                    }}>
                        <Box sx={{
                            p: 3,
                            borderBottom: `1px solid ${theme.palette.divider}`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between'
                        }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                                <Box sx={{ width: 4, height: 20, bgcolor: theme.palette.primary.main, borderRadius: 1 }} />
                                <Typography variant="h6" sx={{ fontSize: '0.9rem', color: theme.palette.text.primary, fontWeight: 800, letterSpacing: '0.05em' }}>
                                    THREAT DISTRIBUTION ANALYTICS
                                </Typography>
                            </Box>
                        </Box>
                        <Box sx={{ flexGrow: 1, p: 4 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                                    <defs>
                                        {chartData.map((entry, index) => (
                                            <linearGradient key={`grad-${index}`} id={`barGradient-${index}`} x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="0%" stopColor={entry.color} stopOpacity={1} />
                                                <stop offset="90%" stopColor={entry.color} stopOpacity={0.6} />
                                            </linearGradient>
                                        ))}
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke={alpha(theme.palette.divider, 0.5)} vertical={false} />
                                    <XAxis
                                        dataKey="name"
                                        tick={{ fill: theme.palette.text.secondary, fontSize: 11, fontWeight: 700, letterSpacing: '0.05em' }}
                                        axisLine={false}
                                        tickLine={false}
                                        dy={15}
                                    />
                                    <YAxis
                                        tick={{ fill: theme.palette.text.secondary, fontSize: 11, fontWeight: 600 }}
                                        axisLine={false}
                                        tickLine={false}
                                    />
                                    <Tooltip
                                        cursor={{ fill: alpha(theme.palette.primary.main, 0.04) }}
                                        contentStyle={{
                                            borderRadius: '16px',
                                            boxShadow: '0 12px 32px rgba(0,0,0,0.12)',
                                            border: `1px solid ${alpha(theme.palette.divider, 0.8)}`,
                                            backdropFilter: 'blur(12px)',
                                            background: alpha('#FFFFFF', 0.9),
                                            padding: '12px 16px'
                                        }}
                                        labelStyle={{ fontWeight: 900, color: theme.palette.text.primary, marginBottom: 4, fontSize: '0.9rem' }}
                                        itemStyle={{ fontWeight: 700, fontSize: '0.8rem' }}
                                    />
                                    <Bar dataKey="value" radius={[8, 8, 0, 0]} barSize={50}>
                                        {chartData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={`url(#barGradient-${index})`} />
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
