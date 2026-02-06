import React, { useEffect, useState, useRef } from 'react';
import { Box, Typography, CircularProgress, Chip, IconButton, MenuItem, Select, FormControl, InputLabel, useTheme, alpha } from '@mui/material';
import { Scan, Target, Activity, Camera, Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';

const LiveFeed = () => {
    const [processedImageSrc, setProcessedImageSrc] = useState(null);
    const [metadata, setMetadata] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [isStreaming, setIsStreaming] = useState(false);
    const [devices, setDevices] = useState([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState('');
    const [permissionError, setPermissionError] = useState(null);
    const theme = useTheme();

    const wsRef = useRef(null);
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamIntervalRef = useRef(null);

    // 1. Get available cameras with permission check
    const getDevices = async () => {
        try {
            // Must ask for permission first to get labels
            await navigator.mediaDevices.getUserMedia({ video: true });

            const devs = await navigator.mediaDevices.enumerateDevices();
            const videoDevs = devs.filter(d => d.kind === 'videoinput');
            setDevices(videoDevs);

            // Auto-select DroidCam if found, otherwise first available
            const droidCam = videoDevs.find(d => d.label.toLowerCase().includes('droidcam'));

            if (!selectedDeviceId) {
                if (droidCam) {
                    setSelectedDeviceId(droidCam.deviceId);
                } else if (videoDevs.length > 0) {
                    setSelectedDeviceId(videoDevs[0].deviceId);
                }
            }
        } catch (err) {
            console.error("Error accessing devices:", err);
        }
    };

    useEffect(() => {
        getDevices();
        return () => stopStream();
    }, []);

    // 2. Handle Camera Stream
    useEffect(() => {
        if (!selectedDeviceId) return;

        // Track if this effect execution is still valid
        let active = true;

        const startCamera = async () => {
            try {
                if (window.currentStream) {
                    window.currentStream.getTracks().forEach(track => track.stop());
                }

                const stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        deviceId: { exact: selectedDeviceId },
                        width: { ideal: 640 },
                        height: { ideal: 480 }
                    }
                });

                if (!active) {
                    // Component unmounted or id changed while loading
                    stream.getTracks().forEach(t => t.stop());
                    return;
                }

                window.currentStream = stream;
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    videoRef.current.onloadedmetadata = () => {
                        if (active && videoRef.current) {
                            videoRef.current.play().catch(e => {
                                if (e.name !== 'AbortError') console.error("Play error:", e);
                            });
                        }
                    };
                }
                // Clear any previous permission errors
                setPermissionError(null);

            } catch (err) {
                console.error("Error accessing camera:", err);
                if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                    setPermissionError("Camera access denied. Please allow permissions in your browser settings.");
                }
            }
        };
        startCamera();

        return () => {
            active = false;
        };
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
        const wsUrl = `ws://localhost:8000/ws/live-feed`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            setIsConnected(true);
            console.log("WS Connected. Ready to stream.");
            startStreaming(ws);
        };

        ws.onmessage = async (event) => {
            // We receive PROCESSED frames back from the server
            if (event.data instanceof Blob) {
                const url = URL.createObjectURL(event.data);
                setProcessedImageSrc(prev => {
                    if (prev) URL.revokeObjectURL(prev);
                    return url;
                });
            } else {
                try {
                    const data = JSON.parse(event.data);
                    setMetadata(data);
                } catch (e) { }
            }
        };

        ws.onclose = () => {
            setIsConnected(false);
            setIsStreaming(false);
            if (streamIntervalRef.current) clearInterval(streamIntervalRef.current);
            setTimeout(connectWebSocket, 3000);
        };
    };

    const startStreaming = (ws) => {
        if (streamIntervalRef.current) clearInterval(streamIntervalRef.current);

        setIsStreaming(true);
        streamIntervalRef.current = setInterval(() => {
            if (
                ws.readyState === WebSocket.OPEN &&
                videoRef.current &&
                canvasRef.current &&
                videoRef.current.readyState === 4 // Ensure video is actually playing
            ) {
                const context = canvasRef.current.getContext('2d');
                context.drawImage(videoRef.current, 0, 0, 640, 480);

                canvasRef.current.toBlob((blob) => {
                    if (blob) {
                        ws.send(blob);
                    }
                }, 'image/jpeg', 0.8);
            } else if (videoRef.current && videoRef.current.paused) {
                // Force play if paused
                videoRef.current.play().catch(e => console.error("Auto-play failed:", e));
            }
        }, 100); // 10 FPS streaming
    };

    const stopStream = () => {
        if (streamIntervalRef.current) clearInterval(streamIntervalRef.current);
        setIsStreaming(false);
    };

    const toggleStream = () => {
        if (isStreaming) {
            stopStream();
        } else if (wsRef.current && isConnected) {
            startStreaming(wsRef.current);
        }
    };

    return (
        <Box sx={{
            position: 'relative',
            width: '100%',
            height: '100%',
            minHeight: 400,
            bgcolor: 'black',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
            borderRadius: 0,
        }}>
            {/* Hidden Source Elements */}
            <video ref={videoRef} autoPlay playsInline muted style={{ display: 'none' }} />
            <canvas ref={canvasRef} width={640} height={480} style={{ display: 'none' }} />

            {/* Scanning Line Animation - Updated Color */}
            {isStreaming && (
                <motion.div
                    style={{
                        position: 'absolute',
                        top: 0, left: 0, right: 0,
                        height: '2px',
                        background: alpha(theme.palette.primary.main, 0.8),
                        boxShadow: `0 0 10px ${theme.palette.primary.main}`,
                        zIndex: 2,
                    }}
                    animate={{ top: ['0%', '100%'] }}
                    transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                />
            )}

            {!isConnected && (
                <Box sx={{ color: theme.palette.text.secondary, textAlign: 'center', zIndex: 3 }}>
                    <CircularProgress color="inherit" />
                    <Typography variant="caption" display="block" sx={{ mt: 1, letterSpacing: '0.1em' }}>
                        CONNECTING SERVER...
                    </Typography>
                </Box>
            )}

            {/* Permission Error Display */}
            {permissionError && (
                <Box sx={{
                    position: 'absolute',
                    zIndex: 20,
                    bgcolor: alpha(theme.palette.error.dark, 0.9),
                    p: 4,
                    borderRadius: 2,
                    textAlign: 'center',
                    border: `1px solid ${theme.palette.error.main}`
                }}>
                    <WifiOff size={48} color={theme.palette.error.main} />
                    <Typography color="error" variant="h6" sx={{ mt: 2 }}>ACCESS DENIED</Typography>
                    <Typography color="white" sx={{ mt: 1 }}>{permissionError}</Typography>
                    <Typography variant="caption" color="white" sx={{ mt: 2, display: 'block', opacity: 0.7 }}>
                        Click the camera icon in your browser address bar to reset permissions.
                    </Typography>
                </Box>
            )}

            {/* Display PROCESSED frame from server */}
            {processedImageSrc && isStreaming ? (
                <img
                    src={processedImageSrc}
                    alt="Processed Stream"
                    style={{ width: '100%', height: '100%', objectFit: 'contain', zIndex: 1 }}
                />
            ) : isConnected && (
                <Box sx={{ color: theme.palette.text.disabled, opacity: 0.5, zIndex: 3, textAlign: 'center' }}>
                    <Camera size={48} />
                    <Typography>Camera Active - Waiting for Stream</Typography>
                </Box>
            )}

            {/* Controls HUD */}
            <Box sx={{ position: 'absolute', top: 16, right: 16, zIndex: 10, display: 'flex', gap: 1 }}>
                <FormControl variant="filled" size="small" sx={{ minWidth: 120, bgcolor: 'rgba(0,0,0,0.5)', borderRadius: 1 }}>
                    <InputLabel sx={{ color: '#aaa' }}>Source</InputLabel>
                    <Select
                        value={selectedDeviceId}
                        onChange={(e) => setSelectedDeviceId(e.target.value)}
                        label="Source"
                        sx={{ color: '#fff', '.MuiSelect-icon': { color: '#fff' } }}
                    >
                        {devices.map((device) => (
                            <MenuItem key={device.deviceId} value={device.deviceId}>
                                {device.label || `Camera ${device.deviceId.slice(0, 5)}...`}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>

                <IconButton
                    onClick={getDevices}
                    title="Refresh Devices"
                    sx={{ bgcolor: 'rgba(255, 255, 255, 0.1)', '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' } }}
                >
                    <RefreshCw size={20} color="#fff" />
                </IconButton>

                <IconButton
                    onClick={toggleStream}
                    sx={{
                        bgcolor: isStreaming ? alpha(theme.palette.primary.main, 0.2) : alpha(theme.palette.error.main, 0.2),
                        '&:hover': { bgcolor: 'rgba(0,0,0,0.5)' }
                    }}
                >
                    {isStreaming ? <Wifi color={theme.palette.primary.main} /> : <WifiOff color={theme.palette.error.main} />}
                </IconButton>
            </Box>


            {/* Metadata HUD */}
            {metadata && isStreaming && (
                <Box sx={{
                    position: 'absolute',
                    bottom: 16,
                    left: 16,
                    right: 16,
                    zIndex: 4,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'end'
                }}>
                    <Box sx={{ bgcolor: 'rgba(0,0,0,0.7)', p: 1.5, borderRadius: 2, border: `1px solid ${alpha(theme.palette.text.secondary, 0.3)}` }}>
                        <Typography variant="caption" color="primary" display="block" sx={{ fontWeight: 600 }}>TARGET ANALYSIS</Typography>
                        <Box sx={{ display: 'flex', gap: 3, mt: 0.5 }}>
                            <Box>
                                <Typography variant="caption" color="text.secondary">PERSONS</Typography>
                                <Typography variant="h6" color="white" sx={{ lineHeight: 1 }}>
                                    {metadata.detections?.person_count || 0}
                                </Typography>
                            </Box>
                            <Box>
                                <Typography variant="caption" color="text.secondary">OBJECTS</Typography>
                                <Typography variant="h6" color="white" sx={{ lineHeight: 1 }}>
                                    {metadata.detections?.object_count || 0}
                                </Typography>
                            </Box>
                        </Box>
                    </Box>

                    <Box sx={{ textAlign: 'right' }}>
                        <Typography variant="caption" color="secondary" display="block" sx={{ mb: 0.5, fontWeight: 600 }}>THREAT LEVEL</Typography>
                        <Typography variant="h3" color={metadata.risk_score > 50 ? 'secondary' : 'primary'} sx={{ fontWeight: 'bold' }}>
                            {metadata.risk_score?.toFixed(0)}%
                        </Typography>
                        {metadata.alert && (
                            <Chip
                                label={metadata.alert.level}
                                color={metadata.alert.level === 'CRITICAL' ? 'error' : 'secondary'}
                                size="small"
                                sx={{ mt: 0.5, fontWeight: 'bold' }}
                            />
                        )}
                    </Box>
                </Box>
            )}

            {/* Center Reticle */}
            <Box sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', opacity: 0.2, pointerEvents: 'none', zIndex: 2 }}>
                <Target color={theme.palette.text.secondary} size={64} strokeWidth={1} />
            </Box>
        </Box>
    );
};

export default LiveFeed;
