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
        const ws = new WebSocket(`ws://localhost:8000/ws/live-feed`);
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
            minHeight: 480,
            bgcolor: '#000',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            borderRadius: 3,
            border: `1px solid ${theme.palette.divider}`,
        }}>
            {/* Header / Toolbar */}
            <Box sx={{
                height: 48,
                bgcolor: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                px: 2,
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
            <Box sx={{ flexGrow: 1, position: 'relative', bgcolor: '#1A1A1A', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>

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
                        height: '100%',
                        objectFit: 'contain'
                    }}
                />

                {/* 2. Canvas (Hidden) */}
                <canvas ref={canvasRef} width={640} height={480} style={{ display: 'none' }} />

                {/* 3. Processed Feed (Visible only if valid source) */}
                {processedImageSrc && isConnected && !cameraError && (
                    <img src={processedImageSrc} alt="Stream" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                )}

                {/* Status Overlay: Connection Wait */}
                {(!processedImageSrc && isConnected && !cameraError && !isOfflineMode) && (
                    <Box sx={{ textAlign: 'center', color: theme.palette.info.main, position: 'absolute' }}>
                        <RefreshCw size={24} className="spin" style={{ animation: 'spin 2s linear infinite' }} />
                        <Typography variant="caption" sx={{ mt: 1, display: 'block', fontWeight: 600 }}>SYNCHRONIZING AI...</Typography>
                    </Box>
                )}

                {/* HUD Overlay - DYNAMIC BACKGROUND */}
                <Box sx={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: 64, // Taller for prominence
                    bgcolor: alpha(getRiskColor(currentScore), 0.85), // Dynamic Background
                    backdropFilter: 'blur(12px)',
                    borderTop: '1px solid rgba(255,255,255,0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    px: 3,
                    opacity: 1,
                    transition: 'background-color 0.5s ease',
                    boxShadow: '0 -4px 20px rgba(0,0,0,0.2)'
                }}>
                    {/* Left: Stats */}
                    <Box sx={{ display: 'flex', gap: 4 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                            <User size={20} color="#fff" strokeWidth={2.5} />
                            <Typography variant="subtitle1" sx={{ color: '#fff', fontWeight: 800, fontFamily: 'monospace' }}>
                                {metadata?.detections?.person_count || 0}
                            </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                            <BoxIcon size={20} color="#fff" strokeWidth={2.5} />
                            <Typography variant="subtitle1" sx={{ color: '#fff', fontWeight: 800, fontFamily: 'monospace' }}>
                                {metadata?.detections?.object_count || 0}
                            </Typography>
                        </Box>
                    </Box>

                    {/* Center: CENTRAL THREAT INDICATOR */}
                    <Box sx={{ position: 'absolute', left: '50%', transform: 'translateX(-50%)', textAlign: 'center' }}>
                        <Typography variant="overline" sx={{ color: 'rgba(255,255,255,0.9)', fontWeight: 700, letterSpacing: '0.15em', lineHeight: 1, display: 'block' }}>
                            THREAT LEVEL
                        </Typography>
                        <Typography variant="h5" sx={{ color: '#fff', fontWeight: 900, letterSpacing: '0.05em', lineHeight: 1, mt: 0.5, textShadow: '0 2px 8px rgba(0,0,0,0.3)' }}>
                            {(currentScore >= 75) ? 'CRITICAL' :
                                (currentScore >= 50) ? 'HIGH' :
                                    (currentScore >= 25) ? 'MEDIUM' : 'LOW'}
                        </Typography>
                    </Box>

                    {/* Right: Percentage */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="h3" sx={{ color: '#fff', fontWeight: 800, fontFamily: 'monospace', letterSpacing: '-0.05em' }}>
                            {currentScore.toFixed(0)}%
                        </Typography>
                    </Box>
                </Box>
            </Box>
        </Box>
    );
};

export default LiveFeed;
