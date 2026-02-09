import React, { useEffect, useState, useRef } from 'react';
import { Box, Typography, CircularProgress, IconButton, MenuItem, Select, FormControl, useTheme, alpha, Button, Tooltip } from '@mui/material';
import { Wifi, WifiOff, Maximize2, User, Box as BoxIcon, AlertTriangle, RefreshCw, EyeOff, Eye, ServerOff } from 'lucide-react';

const LiveFeed = () => {
    const [processedImageSrc, setProcessedImageSrc] = useState(null);
    const [metadata, setMetadata] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [isStreaming, setIsStreaming] = useState(false);
    const [devices, setDevices] = useState([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState('');
    const [cameraError, setCameraError] = useState(null);
    const theme = useTheme();

    const wsRef = useRef(null);
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamIntervalRef = useRef(null);

    // 1. Get Devices
    useEffect(() => {
        const getDevices = async () => {
            try {
                await navigator.mediaDevices.getUserMedia({ video: true });
                const devs = await navigator.mediaDevices.enumerateDevices();
                const videoDevs = devs.filter(d => d.kind === 'videoinput');
                setDevices(videoDevs);
                if (videoDevs.length > 0 && !selectedDeviceId) setSelectedDeviceId(videoDevs[0].deviceId);
            } catch (err) {
                console.error(err);
                setCameraError("Camera access denied. Please check permissions.");
            }
        };
        getDevices();
        return () => stopStream();
    }, []);

    // 2. Start Camera
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
                    await videoRef.current.play().catch(e => console.error("Auto-play blocked:", e));
                }
                setCameraError(null);
            } catch (err) {
                console.error(err);
                setCameraError("Failed to start camera feed.");
            }
        };
        startCamera();
    }, [selectedDeviceId]);

    // 3. Connect to WebSocket
    useEffect(() => {
        connectWebSocket();
        return () => {
            if (wsRef.current) wsRef.current.close();
            if (streamIntervalRef.current) clearInterval(streamIntervalRef.current);
        };
    }, []);

    const connectWebSocket = () => {
        const ws = new WebSocket(`ws://localhost:8001/ws/live-feed`);
        wsRef.current = ws;
        ws.onopen = () => {
            setIsConnected(true);
            setCameraError(null);
            startStreaming(ws);
        };
        ws.onmessage = (event) => {
            if (event.data instanceof Blob) {
                const url = URL.createObjectURL(event.data);
                setProcessedImageSrc(prev => { if (prev) URL.revokeObjectURL(prev); return url; });
            } else {
                try {
                    const data = JSON.parse(event.data);
                    if (data.error) setCameraError(`System Warning: ${data.error}`);
                    setMetadata(prev => ({ ...data, lastUpdated: Date.now() }));
                } catch (e) { }
            }
        };
        ws.onclose = () => {
            setIsConnected(false);
            setTimeout(connectWebSocket, 3000);
        };
        ws.onerror = () => setIsConnected(false);
    };

    const startStreaming = (ws) => {
        if (streamIntervalRef.current) clearInterval(streamIntervalRef.current);
        setIsStreaming(true);
        streamIntervalRef.current = setInterval(() => {
            if (videoRef.current && canvasRef.current) {
                const context = canvasRef.current.getContext('2d');
                if (videoRef.current.readyState === 4) {
                    context.drawImage(videoRef.current, 0, 0, 640, 480);
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        canvasRef.current.toBlob((blob) => {
                            if (blob && ws.readyState === WebSocket.OPEN) ws.send(blob);
                        }, 'image/jpeg', 0.8);
                    }
                }
            }
        }, 100);
    };

    const stopStream = () => {
        if (streamIntervalRef.current) clearInterval(streamIntervalRef.current);
        setIsStreaming(false);
    };

    // Determine current mode
    const isOfflineMode = !isConnected && !cameraError && selectedDeviceId;

    // Helpers for Risk Display
    const currentScore = metadata?.risk_score || 0;
    const getRiskColor = (s) => {
        if (s >= 75) return theme.palette.error.main;
        if (s >= 50) return theme.palette.warning.main;
        if (s >= 25) return theme.palette.info.light;
        return theme.palette.success.light;
    }

    return (
        <Box sx={{
            position: 'relative',
            width: '100%',
            height: '100%',
            bgcolor: '#000',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
        }}>
            {/* Header / Toolbar */}
            <Box sx={{
                height: 32,
                bgcolor: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                px: 1.5,
                borderBottom: `1px solid ${theme.palette.divider}`
            }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            bgcolor: isOfflineMode ? theme.palette.warning.main : ((isConnected && isStreaming) ? theme.palette.success.main : theme.palette.error.main),
                            boxShadow: (isConnected && isStreaming) ? `0 0 8px ${theme.palette.success.main}` : 'none'
                        }} />
                        <Typography variant="caption" sx={{ color: theme.palette.text.primary, fontWeight: 700, letterSpacing: '0.05em' }}>
                            {isOfflineMode ? 'RAW FEED' : (isStreaming ? 'LIVE FEED [ACTIVE]' : 'OFFLINE')}
                        </Typography>
                    </Box>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <FormControl variant="standard" sx={{ minWidth: 120 }}>
                        <Select
                            value={selectedDeviceId}
                            onChange={(e) => setSelectedDeviceId(e.target.value)}
                            disableUnderline
                            sx={{ color: theme.palette.text.secondary, fontSize: '0.75rem', height: 24, fontWeight: 500 }}
                        >
                            <MenuItem value="" disabled>Select Camera</MenuItem>
                            {devices.map((d, i) => <MenuItem key={i} value={d.deviceId}>{d.label.slice(0, 20)}...</MenuItem>)}
                        </Select>
                    </FormControl>
                </Box>
            </Box>

            {/* Video Area */}
            <Box sx={{ flexGrow: 1, position: 'relative', bgcolor: '#000', display: 'flex', alignItems: 'flex-start', justifyContent: 'center', overflow: 'visible' }}>

                {/* 1. Raw Video Element (Fallback logic improved) */}
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    style={{
                        // Show raw video if:
                        // 1. Offline Mode is active
                        // 2. OR we are connected but haven't received a frame yet (processedImageSrc is null)
                        display: (isOfflineMode || !processedImageSrc) ? 'block' : 'none',
                        width: '100%',
                        height: 'auto',
                        maxHeight: 'calc(100% - 72px)',
                        objectFit: 'contain'
                    }}
                />

                {/* 2. Canvas (Hidden) */}
                <canvas ref={canvasRef} width={640} height={480} style={{ display: 'none' }} />

                {/* 3. Processed Feed (Visible only if valid source) */}
                {processedImageSrc && isConnected && !cameraError && (
                    <img src={processedImageSrc} alt="Stream" style={{ width: '100%', height: 'auto', maxHeight: 'calc(100% - 72px)', objectFit: 'contain' }} />
                )}

                {/* Status Overlay: Connection Wait */}
                {(!processedImageSrc && isConnected && !cameraError && !isOfflineMode) && (
                    <Box sx={{ textAlign: 'center', color: theme.palette.info.main, position: 'absolute' }}>
                        <RefreshCw size={24} className="spin" style={{ animation: 'spin 2s linear infinite' }} />
                        <Typography variant="caption" sx={{ mt: 1, display: 'block', fontWeight: 600 }}>SYNCHRONIZING AI...</Typography>
                    </Box>
                )}

                {/* HUD Overlay - PREMIUM HIGH-TECH DESIGN */}
                <Box sx={{
                    position: 'absolute',
                    bottom: 35,
                    left: 0,
                    right: 0,
                    height: 72,
                    // Rich Gradient Background based on Risk
                    background: `linear-gradient(to top, 
                        ${alpha(getRiskColor(currentScore), 0.9)} 0%, 
                        ${alpha(getRiskColor(currentScore), 0.4)} 100%)`,
                    backdropFilter: 'blur(16px) saturate(180%)',
                    borderTop: '1px solid rgba(255,255,255,0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    px: 4,
                    transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
                    boxShadow: `0 -8px 32px ${alpha(getRiskColor(currentScore), 0.3)}`
                }}>
                    {/* Left: Stats with Glow */}
                    <Box sx={{ display: 'flex', gap: 4 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, opacity: 0.9 }}>
                            <User size={18} color="#fff" strokeWidth={2.5} />
                            <Typography variant="h6" sx={{ color: '#fff', fontWeight: 900, fontFamily: 'monospace', fontSize: '1.1rem' }}>
                                {metadata?.detections?.person_count || 0}
                            </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, opacity: 0.9 }}>
                            <BoxIcon size={18} color="#fff" strokeWidth={2.5} />
                            <Typography variant="h6" sx={{ color: '#fff', fontWeight: 900, fontFamily: 'monospace', fontSize: '1.1rem' }}>
                                {metadata?.detections?.object_count || 0}
                            </Typography>
                        </Box>
                    </Box>

                    {/* Center: CENTRAL THREAT INDICATOR */}
                    <Box sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        position: 'absolute',
                        left: '50%',
                        transform: 'translateX(-50%)'
                    }}>
                        <Typography variant="overline" sx={{
                            color: 'rgba(255,255,255,0.7)',
                            fontWeight: 800,
                            letterSpacing: '0.2em',
                            lineHeight: 1,
                            fontSize: '0.65rem'
                        }}>
                            STATUS
                        </Typography>
                        <Typography variant="h6" sx={{
                            color: '#fff',
                            fontWeight: 900,
                            letterSpacing: '0.1em',
                            lineHeight: 1,
                            mt: 0.5,
                            textShadow: '0 0 12px rgba(255,255,255,0.4)',
                            fontSize: '0.9rem'
                        }}>
                            {(currentScore >= 75) ? 'CRITICAL BREACH' :
                                (currentScore >= 50) ? 'ELEVATED RISK' :
                                    (currentScore >= 25) ? 'CAUTION REQ' : 'SECURE'}
                        </Typography>
                    </Box>

                    {/* Right: Percentage - High Visibility */}
                    <Box sx={{
                        display: 'flex',
                        alignItems: 'baseline',
                        gap: 1,
                        bgcolor: 'rgba(255,255,255,0.15)',
                        px: 2,
                        py: 0.5,
                        borderRadius: 2,
                        border: '1px solid rgba(255,255,255,0.2)'
                    }}>
                        <Typography variant="overline" sx={{
                            color: 'rgba(255,255,255,0.8)',
                            fontWeight: 900,
                            fontSize: '0.7rem'
                        }}>
                            THREAT
                        </Typography>
                        <Typography variant="h3" sx={{
                            color: '#fff',
                            fontWeight: 900,
                            fontFamily: 'monospace',
                            lineHeight: 1,
                            fontSize: '2rem',
                            textShadow: '0 0 20px rgba(255,255,255,0.3)'
                        }}>
                            {Math.round(currentScore)}%
                        </Typography>
                    </Box>
                </Box>
            </Box>
        </Box>
    );
};

export default LiveFeed;

