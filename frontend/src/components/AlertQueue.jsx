import React, { useState } from 'react';
import {
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Chip,
    Button,
    Box,
    Typography,
    IconButton,
    useTheme,
    alpha
} from '@mui/material';
import { Warning, CheckCircle, MoreVertical } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const AlertQueue = ({ alerts, onAcknowledge }) => {
    const [selectedAlert, setSelectedAlert] = useState(null);
    const theme = useTheme();

    const getAlertColor = (level) => {
        const colors = {
            'CRITICAL': 'error',
            'HIGH': 'warning',
            'MEDIUM': 'info',
            'LOW': 'success'
        };
        return colors[level] || 'default';
    };

    const handleAcknowledge = async (alertId) => {
        try {
            await fetch(`http://localhost:8000/alerts/${alertId}/acknowledge`, {
                method: 'POST'
            });
            onAcknowledge();
        } catch (error) {
            console.error('Error acknowledging alert:', error);
        }
    };

    return (
        <Box>
            <TableContainer sx={{ maxHeight: 400 }}>
                <Table stickyHeader size="small">
                    <TableHead>
                        <TableRow>
                            {['TIMESTAMP', 'THREAT LEVEL', 'RISK SCORE', 'CAMERA ID', 'STATUS', 'ACTION'].map((head) => (
                                <TableCell
                                    key={head}
                                    sx={{
                                        bgcolor: theme.palette.background.paper,
                                        color: theme.palette.text.secondary,
                                        borderBottom: `1px solid ${theme.palette.divider}`,
                                        fontWeight: 600,
                                        py: 1.5
                                    }}
                                >
                                    {head}
                                </TableCell>
                            ))}
                        </TableRow>
                    </TableHead>
                    <TableBody component={motion.tbody}>
                        <AnimatePresence>
                            {alerts.map((alert) => (
                                <TableRow
                                    key={alert.id}
                                    component={motion.tr}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0 }}
                                    transition={{ duration: 0.2 }}
                                    hover
                                    onClick={() => setSelectedAlert(alert)}
                                    sx={{
                                        cursor: 'pointer',
                                        '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.05) + ' !important' },
                                        transition: 'background-color 0.2s',
                                    }}
                                >
                                    <TableCell sx={{ borderBottom: `1px solid ${theme.palette.divider}`, color: theme.palette.text.primary, py: 1.5 }}>
                                        {new Date(alert.timestamp).toLocaleTimeString()}
                                    </TableCell>
                                    <TableCell sx={{ borderBottom: `1px solid ${theme.palette.divider}`, py: 1.5 }}>
                                        <Chip
                                            label={alert.level}
                                            color={getAlertColor(alert.level)}
                                            size="small"
                                            variant={alert.level === 'CRITICAL' ? 'filled' : 'outlined'}
                                            sx={{ fontWeight: 'bold', borderRadius: '8px' }}
                                        />
                                    </TableCell>
                                    <TableCell sx={{ borderBottom: `1px solid ${theme.palette.divider}`, py: 1.5 }}>
                                        <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                                            <Typography
                                                variant="body2"
                                                sx={{
                                                    fontWeight: 'bold',
                                                    color: alert.risk_score > 75 ? theme.palette.error.main : theme.palette.success.main,
                                                }}
                                            >
                                                {alert.risk_score.toFixed(1)}
                                            </Typography>
                                        </Box>
                                    </TableCell>
                                    <TableCell sx={{ borderBottom: `1px solid ${theme.palette.divider}`, fontFamily: 'monospace', color: theme.palette.text.secondary, py: 1.5 }}>{alert.camera_id}</TableCell>
                                    <TableCell sx={{ borderBottom: `1px solid ${theme.palette.divider}`, py: 1.5 }}>
                                        <Chip
                                            label={alert.status}
                                            size="small"
                                            sx={{
                                                bgcolor: alert.status === 'acknowledged' ? alpha(theme.palette.success.main, 0.1) : alpha(theme.palette.action.disabled, 0.1),
                                                color: alert.status === 'acknowledged' ? theme.palette.success.main : theme.palette.text.disabled,
                                                border: '1px solid',
                                                borderColor: alert.status === 'acknowledged' ? theme.palette.success.main : theme.palette.divider
                                            }}
                                        />
                                    </TableCell>
                                    <TableCell sx={{ borderBottom: `1px solid ${theme.palette.divider}`, py: 1.5 }}>
                                        {alert.status === 'pending' && (
                                            <Button
                                                size="small"
                                                sx={{ minWidth: 0, p: 0.5, color: theme.palette.primary.main }}
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleAcknowledge(alert.id);
                                                }}
                                            >
                                                <CheckCircle size={18} />
                                            </Button>
                                        )}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </AnimatePresence>
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
};

export default AlertQueue;
