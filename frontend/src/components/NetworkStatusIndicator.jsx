import React, { useState, useEffect } from 'react';
import { Box, Typography, alpha, useTheme, Slide } from '@mui/material';
import { Wifi, WifiOff, Globe, Zap } from 'lucide-react';

const NetworkStatusIndicator = () => {
    const [isOnline, setIsOnline] = useState(navigator.onLine);
    const [showIndicator, setShowIndicator] = useState(false);
    const theme = useTheme();

    useEffect(() => {
        const handleOnline = () => {
            setIsOnline(true);
            setShowIndicator(true);
            setTimeout(() => setShowIndicator(false), 5000); // Hide after 5 seconds of being back online
        };
        const handleOffline = () => {
            setIsOnline(false);
            setShowIndicator(true);
        };

        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        if (!isOnline) setShowIndicator(true);

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, [isOnline]);

    return (
        <Slide direction="up" in={showIndicator} mountOnEnter unmountOnExit>
            <Box sx={{
                position: 'fixed',
                bottom: 24,
                left: 24,
                zIndex: 2000,
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                px: 2.5,
                py: 1.5,
                bgcolor: alpha(isOnline ? theme.palette.success.main : theme.palette.error.main, 0.9),
                backdropFilter: 'blur(12px)',
                borderRadius: '16px',
                boxShadow: `0 8px 32px ${alpha(isOnline ? theme.palette.success.main : theme.palette.error.main, 0.3)}`,
                border: `1px solid ${alpha('#FFFFFF', 0.2)}`,
                color: '#fff',
            }}>
                <Box sx={{
                    display: 'flex',
                    p: 1,
                    bgcolor: alpha('#FFFFFF', 0.2),
                    borderRadius: '12px',
                }}>
                    {isOnline ? <Wifi size={20} /> : <WifiOff size={20} />}
                </Box>
                <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 800, lineHeight: 1.2, letterSpacing: '0.02em' }}>
                        {isOnline ? 'SYSTEM ONLINE' : 'OFFLINE MODE'}
                    </Typography>
                    <Typography variant="caption" sx={{ opacity: 0.8, fontWeight: 600, fontSize: '0.65rem' }}>
                        {isOnline ? 'Cloud sync active & processing' : 'Local processing only - Sync paused'}
                    </Typography>
                </Box>
                {isOnline && (
                    <Box sx={{
                        ml: 1,
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        bgcolor: '#fff',
                        animation: 'pulse 2s infinite'
                    }} />
                )}

                <style>
                    {`
                    @keyframes pulse {
                        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7); }
                        70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(255, 255, 255, 0); }
                        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
                    }
                    `}
                </style>
            </Box>
        </Slide>
    );
};

export default NetworkStatusIndicator;
