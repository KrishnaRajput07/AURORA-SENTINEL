import React from 'react';
import { Box, Grid, Typography, Card, CardContent, useTheme } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Activity, AlertOctagon } from 'lucide-react';

const AnalyticsDashboard = ({ data }) => {
    const theme = useTheme();
    if (!data) return <Typography>Loading Analytics...</Typography>;

    const { total_alerts, critical_alerts, alert_levels } = data;

    const chartData = [
        { name: 'Critical', value: alert_levels?.critical || 0, color: theme.palette.error.main },
        { name: 'High', value: alert_levels?.high || 0, color: theme.palette.warning.main },
        { name: 'Medium', value: alert_levels?.medium || 0, color: theme.palette.info.main },
        { name: 'Low', value: alert_levels?.low || 0, color: theme.palette.success.main },
    ];

    const StatCard = ({ title, value, icon: Icon, color }) => (
        <Card sx={{
            bgcolor: 'rgba(255,255,255,0.03)',
            border: `1px solid ${color}`,
            background: `linear-gradient(135deg, rgba(255,255,255,0.03) 0%, ${color}22 100%)`
        }}>
            <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                    <Typography color="text.secondary" variant="caption" sx={{ textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                        {title}
                    </Typography>
                    <Typography variant="h4" sx={{ color: '#fff', fontWeight: 'bold', mt: 1 }}>
                        {value}
                    </Typography>
                </Box>
                <Box sx={{
                    p: 1.5,
                    borderRadius: '50%',
                    bgcolor: `${color}22`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <Icon color={color} size={24} />
                </Box>
            </CardContent>
        </Card>
    );

    return (
        <Box sx={{ width: '100%' }}>
            <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                    <StatCard
                        title="Total Alerts"
                        value={total_alerts}
                        icon={Activity}
                        color={theme.palette.primary.main}
                    />
                </Grid>
                <Grid item xs={6} md={3}>
                    <StatCard
                        title="Critical Threats"
                        value={critical_alerts}
                        icon={AlertOctagon}
                        color={theme.palette.error.main}
                    />
                </Grid>

                <Grid item xs={12} md={6}>
                    <Box sx={{ height: 200, mt: 0, p: 2, bgcolor: 'rgba(255,255,255,0.02)', borderRadius: 2 }}>
                        <Typography variant="caption" sx={{ letterSpacing: '0.1em', mb: 2, display: 'block', color: '#888' }}>
                            ALERT DISTRIBUTION
                        </Typography>
                        <ResponsiveContainer width="100%" height="80%">
                            <BarChart data={chartData}>
                                <XAxis dataKey="name" tick={{ fill: '#666', fontSize: 12 }} axisLine={false} tickLine={false} />
                                <YAxis hide />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0b1221', border: '1px solid #333', borderRadius: '4px' }}
                                    itemStyle={{ color: '#fff' }}
                                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                />
                                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                                    {chartData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </Box>
                </Grid>
            </Grid>
        </Box>
    );
};

export default AnalyticsDashboard;
