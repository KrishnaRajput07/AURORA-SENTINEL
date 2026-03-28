import React, { useEffect, useState, useRef } from 'react';
import { Box, Typography, useTheme, alpha, MenuItem, Select, FormControl, Switch, FormControlLabel, Fade } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Box as BoxIcon, RefreshCw, BrainCircuit, ShieldCheck } from 'lucide-react';
import { useNotifications } from '../context/NotificationContext';
import { useSettings } from '../context/SettingsContext';
import { WS_BASE_URL } from '../config';

// Global Event Emitter for high-frequency, low-latency UI updates without React layout thrashing
export const threatEventEmitter = new EventTarget();

const LiveFeed = ({ isExpanded }) => {
    const { addNotification } = useNotifications();
    const [metadata, setMetadata] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [devices, setDevices] = useState([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState('');
    const [cameraError, setCameraError] = useState(null);
    const { performanceMode } = useSettings();
    const [vlmMode, setVlmMode] = useState(false); // NEW: VLM Mode State
    const [vitalityPulse, setVitalityPulse] = useState(2);
    const theme = useTheme();

    const wsRef = useRef(null);
    const videoRef = useRef(null);
    const captureCanvasRef = useRef(null);
    const displayCanvasRef = useRef(null);
    const requestRef = useRef(null);
    const isWaitingRef = useRef(false);
    const lastFrameTimeRef = useRef(0);

    // Vitality Pulse
    useEffect(() => {
        const interval = setInterval(() => {
            setVitalityPulse(prev => {
                const change = Math.random() > 0.5 ? 0.5 : -0.5;
                return Math.min(4, Math.max(1, prev + change));
            });
        }, 1500);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (cameraError) {
            addNotification({ title: `Camera Error: ${cameraError.slice(0, 30)}...`, level: 'Critical' });
        }
    }, [cameraError, addNotification]);

    // Initialize Devices
    useEffect(() => {
        const getDevices = async () => {
            try {
                await navigator.mediaDevices.getUserMedia({ video: true });
                const devs = await navigator.mediaDevices.enumerateDevices();
                const videoDevs = devs.filter(d => d.kind === 'videoinput');
                setDevices(videoDevs);
                if (videoDevs.length > 0 && !selectedDeviceId) setSelectedDeviceId(videoDevs[0].deviceId);
            } catch (err) {
                setCameraError("Camera access denied.");
            }
        };
        getDevices();
        return () => {
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
            if (wsRef.current) wsRef.current.close();
        };
    }, []);

    // Start Camera
    useEffect(() => {
        if (!selectedDeviceId) return;
        const startCamera = async () => {
            try {
                if (window.currentStream) window.currentStream.getTracks().forEach(track => track.stop());
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { deviceId: { exact: selectedDeviceId }, width: { ideal: 640 }, height: { ideal: 480 } }
                });
                window.currentStream = stream;
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    await videoRef.current.play();
                }
                setCameraError(null);
            } catch (err) {
                setCameraError("Failed to start camera feed.");
            }
        };
        startCamera();
    }, [selectedDeviceId]);

    // WebSocket & Loop
    useEffect(() => {
        const connect = () => {
            // Dynamic URL based on mode
            const url = vlmMode ? `${WS_BASE_URL}/vlm/vlm-feed` : `${WS_BASE_URL}/ws/live-feed`;
            const ws = new WebSocket(url);
            wsRef.current = ws;

            ws.onopen = () => setIsConnected(true);
            ws.onclose = () => {
                setIsConnected(false);
                setTimeout(connect, 3000);
            };

            ws.onmessage = async (event) => {
                if (event.data instanceof Blob) {
                    // Optimized: Draw directly to canvas
                    const img = new Image();
                    img.onload = () => {
                        if (displayCanvasRef.current) {
                            const canvas = displayCanvasRef.current;
                            if (canvas.width !== img.width || canvas.height !== img.height) {
                                canvas.width = img.width;
                                canvas.height = img.height;
                            }
                            const ctx = canvas.getContext('2d');
                            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                        }
                        isWaitingRef.current = false;
                        URL.revokeObjectURL(img.src);
                    };
                    img.src = URL.createObjectURL(event.data);
                } else {
                    try {
                        const data = JSON.parse(event.data);
                        setMetadata(data);
                        
                        // Fire event so separate components (like HotThreatsCard) can listen without triggering a global re-render loop
                        if (data?.detections?.active_threats) {
                            threatEventEmitter.dispatchEvent(new CustomEvent('threatsUpdated', { detail: data.detections.active_threats }));
                        }
                    } catch (e) { }
                }
            };
        };

        connect();
        requestRef.current = requestAnimationFrame(animate);

        return () => {
            if (wsRef.current) wsRef.current.close();
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
        };
    }, [performanceMode, vlmMode]); // Re-connect when mode changes

    const lastAlertTimeRef = useRef(0);

    const animate = (time) => {
        const frameInterval = performanceMode ? 50 : 0; // Run un-capped for max smoothness if not performanceMode
        
        if (!isWaitingRef.current && (time - lastFrameTimeRef.current >= frameInterval)) {
            captureAndSend();
            lastFrameTimeRef.current = time;
        }

        // Monitoring risk for notifications
        if (currentScore >= 75 && Date.now() - lastAlertTimeRef.current > 30000) {
            addNotification({
                title: `Critical Threat Detected: ${Math.round(currentScore)}% Risk`,
                level: 'Critical',
                source: 'Live Feed'
            });
            lastAlertTimeRef.current = Date.now();
        } else if (currentScore >= 50 && currentScore < 75 && Date.now() - lastAlertTimeRef.current > 60000) {
            addNotification({
                title: `Elevated Risk Pattern: ${Math.round(currentScore)}%`,
                level: 'Warning',
                source: 'Live Feed'
            });
            lastAlertTimeRef.current = Date.now();
        }
        
        // Safety watchdog: Unlock if stuck for > 2 seconds
        if (isWaitingRef.current && (time - lastFrameTimeRef.current > 2000)) {
            isWaitingRef.current = false; 
        }
        requestRef.current = requestAnimationFrame(animate);
    };

    const captureAndSend = () => {
        // Relax readystate check (3 or 4 is fine for processing) and unlock if waiting!
        if (isWaitingRef.current || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        if (!videoRef.current || videoRef.current.readyState < 2) return;

        // Synchronously lock queue before async operations to prevent frame spamming
        isWaitingRef.current = true;

        const canvas = captureCanvasRef.current;
        const video = videoRef.current;
        if (!canvas) {
            isWaitingRef.current = false;
            return;
        }

        const ctx = canvas.getContext('2d');
        const width = performanceMode ? 320 : 640;
        const height = performanceMode ? 240 : 480;

        if (canvas.width !== width) {
            canvas.width = width;
            canvas.height = height;
        }

        ctx.drawImage(video, 0, 0, width, height);
        canvas.toBlob((blob) => {
            if (blob && wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(blob);
            } else {
                // If it fails to send, unlock immediately
                isWaitingRef.current = false;
            }
        }, 'image/jpeg', performanceMode ? 0.6 : 0.82);
    };

    const realScore = metadata?.risk_score || 0;
    const currentScore = Math.max(realScore, vitalityPulse);

    const getRiskColor = (s) => {
        if (s >= 75) return theme.palette.error.main;
        if (s >= 50) return theme.palette.warning.main;
        if (s >= 25) return theme.palette.info.light;
        return theme.palette.success.light;
    };

    return (
        <Box className="live-feed-root" sx={{ 
            position: 'relative', 
            width: '100%', 
            flexGrow: 1, 
            minHeight: '100%', 
            bgcolor: '#000', 
            display: 'flex', 
            flexDirection: 'row', 
            overflow: 'hidden',
            '&:fullscreen': {
                '& .live-feed-header': {
                    display: 'none !important'
                }
            }
        }}>
            {/* MAIN VIDEO FEED AREA */}
            <Box sx={{ 
                flexGrow: 1, 
                display: 'flex', 
                flexDirection: 'column', 
                position: 'relative', 
                overflow: 'hidden' 
            }}>
                {/* Compact Header - Hide when fullscreen */}
                <Box 
                    className="live-feed-header"
                    sx={{ 
                        height: 40, 
                        bgcolor: 'rgba(0, 0, 0, 0.8)', 
                        backdropFilter: 'blur(8px)',
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'space-between', 
                        px: 2, 
                        borderBottom: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        zIndex: 10,
                        transition: 'all 0.3s ease'
                    }}
                >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ 
                            width: 6, 
                            height: 6, 
                            borderRadius: '50%', 
                            bgcolor: isConnected ? theme.palette.success.main : theme.palette.error.main, 
                            boxShadow: isConnected ? `0 0 6px ${alpha(theme.palette.success.main, 0.5)}` : 'none',
                            animation: isConnected ? 'pulse 2s infinite' : 'none'
                        }} />
                        <Typography variant="caption" sx={{ 
                            color: '#fff', 
                            fontWeight: 600, 
                            fontSize: '0.7rem',
                            textShadow: '0 1px 2px rgba(0,0,0,0.5)'
                        }}>
                            {isConnected ? 'LIVE' : 'CONNECTING'}
                        </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <FormControl variant="standard" size="small">
                            <Select 
                                value={selectedDeviceId} 
                                onChange={(e) => setSelectedDeviceId(e.target.value)} 
                                disableUnderline 
                                sx={{ 
                                    fontSize: '0.7rem', 
                                    height: 28,
                                    color: '#fff',
                                    '& .MuiSvgIcon-root': { fontSize: '1rem' },
                                    '&:before': { borderBottomColor: alpha('#fff', 0.3) }
                                }}
                            >
                                {devices.map((d, i) => (
                                    <MenuItem key={i} value={d.deviceId} sx={{ fontSize: '0.7rem' }}>
                                        {d.label.slice(0, 15)}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>

                        {/* VLM Toggle */}
                        <FormControlLabel
                            control={
                                <Switch
                                    checked={vlmMode}
                                    onChange={(e) => setVlmMode(e.target.checked)}
                                    size="small"
                                    color="warning"
                                />
                            }
                            label={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                    <BrainCircuit size={12} color={vlmMode ? theme.palette.warning.main : '#fff'} />
                                    <Typography variant="caption" sx={{ 
                                        fontWeight: 600, 
                                        color: vlmMode ? theme.palette.warning.main : '#fff',
                                        fontSize: '0.65rem'
                                    }}>
                                        AI
                                    </Typography>
                                </Box>
                            }
                            sx={{ mr: 0, ml: 0.5 }}
                        />
                    </Box>
                </Box>

                <Box sx={{ 
                    flexGrow: 1, 
                    position: 'relative', 
                    bgcolor: '#05050A', 
                    backgroundImage: `radial-gradient(circle at 10% 50%, ${alpha(getRiskColor(currentScore), 0.15)} 0%, transparent 60%), radial-gradient(circle at 90% 50%, ${alpha(getRiskColor(currentScore), 0.10)} 0%, transparent 60%)`,
                    display: 'flex', 
                    justifyContent: 'center', 
                    alignItems: 'center', 
                    overflow: 'hidden' 
                }}>
                    <video ref={videoRef} hidden playsInline muted />
                    <canvas ref={captureCanvasRef} style={{ display: 'none' }} />
                    <canvas ref={displayCanvasRef} style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'contain', zIndex: 1 }} />

                    {/* THREAT CONTEXT SIDE PANEL (Visible only when expanded) */}
                    <AnimatePresence>
                        {isExpanded && (
                            <motion.div
                                initial={{ x: -300, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                exit={{ x: -300, opacity: 0 }}
                                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                                style={{
                                    position: 'absolute',
                                    left: 0,
                                    top: 0,
                                    bottom: 0,
                                    width: '320px',
                                    zIndex: 10,
                                    background: 'rgba(20, 20, 25, 0.25)',
                                    backdropFilter: 'blur(30px) saturate(200%)',
                                    WebkitBackdropFilter: 'blur(30px) saturate(200%)',
                                    borderRight: `1px solid rgba(255, 255, 255, 0.1)`,
                                    boxShadow: 'inset -2px 0 20px rgba(255, 255, 255, 0.02), 10px 0 40px rgba(0, 0, 0, 0.5)',
                                    padding: '24px',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    overflowY: 'auto',
                                    pointerEvents: 'auto'
                                }}
                            >
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                                    <ShieldCheck size={24} color={getRiskColor(currentScore)} />
                                    <Typography variant="h6" sx={{ color: '#fff', fontWeight: 800, letterSpacing: '0.05em' }}>
                                        THREAT ANALYSIS
                                    </Typography>
                                </Box>

                                <Box sx={{ textAlign: 'center', mb: 4, p: 2, bgcolor: 'rgba(255,255,255,0.05)', borderRadius: 2, border: `1px solid ${alpha(getRiskColor(currentScore), 0.3)}` }}>
                                    <Typography variant="overline" sx={{ color: 'rgba(255,255,255,0.6)', fontWeight: 700 }}>OVERALL RISK SCORE</Typography>
                                    <Typography variant="h2" sx={{ color: getRiskColor(currentScore), fontWeight: 900, fontFamily: 'monospace', textShadow: `0 0 20px ${alpha(getRiskColor(currentScore), 0.5)}` }}>
                                        {Math.round(currentScore)}<span style={{ fontSize: '0.5em' }}>%</span>
                                    </Typography>
                                </Box>

                                <Typography variant="overline" sx={{ color: 'rgba(255,255,255,0.5)', fontWeight: 700, mb: 1, display: 'block' }}>ACTIVE RISK FACTORS</Typography>
                                
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                    {metadata?.risk_factors && Object.entries(metadata.risk_factors).map(([factor, score]) => {
                                        if (score <= 0.05) return null; // Hide insignificant factors
                                        const percentage = Math.round(score * 100);
                                        const formattedName = factor.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
                                        
                                        return (
                                            <Box key={factor} sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                    <Typography variant="caption" sx={{ color: '#fff', fontWeight: 700 }}>{formattedName}</Typography>
                                                    <Typography variant="caption" sx={{ color: getRiskColor(percentage), fontFamily: 'monospace', fontWeight: 800 }}>{percentage}%</Typography>
                                                </Box>
                                                <Box sx={{ width: '100%', height: 6, bgcolor: 'rgba(255,255,255,0.1)', borderRadius: 3, overflow: 'hidden' }}>
                                                    <motion.div 
                                                        initial={{ width: 0 }}
                                                        animate={{ width: `${percentage}%` }}
                                                        transition={{ duration: 0.5 }}
                                                        style={{ height: '100%', backgroundColor: getRiskColor(percentage), borderRadius: 3 }}
                                                    />
                                                </Box>
                                            </Box>
                                        );
                                    })}
                                    {(!metadata?.risk_factors || Object.values(metadata.risk_factors).every(s => s <= 0.05)) && (
                                        <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.4)', fontStyle: 'italic', textAlign: 'center', py: 2 }}>
                                            No significant risk factors detected at this moment.
                                        </Typography>
                                    )}
                                </Box>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {!isConnected && (
                        <Box sx={{ position: 'absolute', textAlign: 'center', color: '#fff', zIndex: 11 }}>
                            <RefreshCw size={24} className="spin" style={{ animation: 'spin 2s linear infinite' }} />
                            <Typography variant="caption" sx={{ mt: 1, display: 'block', fontWeight: 800 }}>CONNECTING TO SERVER...</Typography>
                            <Typography variant="caption" sx={{ color: theme.palette.warning.main, display: 'block', mt: 0.5 }}>
                                INITIALIZING AI MODELS ON GPU (MAY TAKE 15-30 SECONDS)
                            </Typography>
                        </Box>
                    )}

                    {isConnected && !metadata && (
                        <Box sx={{ position: 'absolute', textAlign: 'center', color: '#fff' }}>
                            <BrainCircuit size={24} className="pulse" style={{ animation: 'pulse 1.5s infinite' }} />
                            <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>{metadata?.error || "MODELS LOADING..."}</Typography>
                        </Box>
                    )}

                    {/* VLM Narrative Overlay */}
                    <Fade in={vlmMode && metadata?.vlm_narrative}>
                        <Box sx={{
                            position: 'absolute',
                            top: 16,
                            left: 16,
                            right: 16,
                            bgcolor: 'rgba(0,0,0,0.8)',
                            backdropFilter: 'blur(8px)',
                            borderLeft: `3px solid ${theme.palette.warning.main}`,
                            p: 1.5,
                            borderRadius: 1,
                            maxWidth: 400
                        }}>
                            <Typography variant="overline" sx={{ 
                                color: theme.palette.warning.main, 
                                fontWeight: 900, 
                                display: 'flex', 
                                alignItems: 'center', 
                                gap: 0.5,
                                fontSize: '0.7rem',
                                mb: 0.5
                            }}>
                                <BrainCircuit size={14} /> LIVE SCENE ANALYSIS ({metadata?.provider?.toUpperCase() || 'AI'})
                            </Typography>
                            <Typography variant="body2" sx={{ 
                                color: '#fff', 
                                fontFamily: 'monospace', 
                                lineHeight: 1.3,
                                fontSize: '0.8rem'
                            }}>
                                {metadata?.vlm_narrative || "Analyzing scene components..."}
                            </Typography>
                        </Box>
                    </Fade>

                    {/* Compact Threat Indicator */}
                    <Box className="threat-indicator-overlay" sx={{
                        position: 'absolute',
                        bottom: 12,
                        left: 12,
                        right: 12,
                        minHeight: 48,
                        zIndex: 100,
                        background: `linear-gradient(to top, ${alpha(getRiskColor(currentScore), 0.95)} 0%, ${alpha(getRiskColor(currentScore), 0.6)} 100%)`,
                        backdropFilter: 'blur(12px)',
                        borderRadius: 2,
                        border: '1px solid rgba(255,255,255,0.15)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        px: 1.5,
                        py: 0.5,
                        boxShadow: '0 4px 20px rgba(0,0,0,0.4)'
                    }}>
                        <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <User size={14} color="#fff" />
                                <Typography variant="body2" sx={{ 
                                    color: '#fff', 
                                    fontWeight: 800, 
                                    fontFamily: 'monospace',
                                    fontSize: '0.8rem'
                                }}>
                                    {metadata?.detections?.person_count || 0}
                                </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <BoxIcon size={14} color="#fff" />
                                <Typography variant="body2" sx={{ 
                                    color: '#fff', 
                                    fontWeight: 800, 
                                    fontFamily: 'monospace',
                                    fontSize: '0.8rem'
                                }}>
                                    {metadata?.detections?.object_count || 0}
                                </Typography>
                            </Box>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="caption" sx={{ 
                                color: 'rgba(255,255,255,0.8)', 
                                fontWeight: 800, 
                                fontSize: '0.65rem',
                                mr: 0.5
                            }}>
                                {currentScore >= 75 ? 'CRITICAL' : (currentScore >= 50) ? 'ELEVATED' : (currentScore >= 25) ? 'CAUTION' : 'SECURE'}
                            </Typography>
                            <Box sx={{ 
                                display: 'flex', 
                                alignItems: 'baseline', 
                                gap: 0.5, 
                                bgcolor: 'rgba(255,255,255,0.2)', 
                                px: 1, 
                                py: 0.25, 
                                borderRadius: 1.5
                            }}>
                                <Typography variant="h6" sx={{ 
                                    color: '#fff', 
                                    fontWeight: 900, 
                                    fontFamily: 'monospace',
                                    fontSize: '1rem'
                                }}>
                                    {Math.round(currentScore)}%
                                </Typography>
                            </Box>
                        </Box>
                    </Box>

                    {/* CSS Animations */}
                    <style>{`
                        @keyframes spin { 
                            from { transform: rotate(0deg); } 
                            to { transform: rotate(360deg); } 
                        }
                        @keyframes pulse { 
                            0%, 100% { opacity: 1; } 
                            50% { opacity: 0.5; } 
                        }
                        .live-feed-root:fullscreen {
                            background: #000 !important;
                        }
                        .live-feed-root:fullscreen .live-feed-header {
                            display: none !important;
                        }
                        .live-feed-root:fullscreen .threat-indicator-overlay {
                            bottom: 8px;
                            left: 8px;
                            right: 8px;
                        }
                    `}</style>
                </Box>
            </Box>
        </Box>
    );
};

export default LiveFeed;
