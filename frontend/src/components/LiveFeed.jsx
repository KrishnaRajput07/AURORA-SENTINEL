import React, { useEffect, useState, useRef } from 'react';
import { Box, Typography, useTheme, alpha, MenuItem, Select, FormControl } from '@mui/material';
import { User, Box as BoxIcon, RefreshCw } from 'lucide-react';
import { useNotifications } from '../context/NotificationContext';
import { useSettings } from '../context/SettingsContext';

const LiveFeed = () => {
    const { addNotification } = useNotifications();
    const [metadata, setMetadata] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [devices, setDevices] = useState([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState('');
    const [cameraError, setCameraError] = useState(null);
    const { performanceMode } = useSettings();
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
            const ws = new WebSocket(`ws://localhost:8000/ws/live-feed`);
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
                            const ctx = displayCanvasRef.current.getContext('2d');
                            displayCanvasRef.current.width = img.width;
                            displayCanvasRef.current.height = img.height;
                            ctx.drawImage(img, 0, 0);
                        }
                        isWaitingRef.current = false;
                        URL.revokeObjectURL(img.src);
                    };
                    img.src = URL.createObjectURL(event.data);
                } else {
                    try {
                        const data = JSON.parse(event.data);
                        setMetadata(data);
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
    }, [performanceMode]);

    const animate = (time) => {
        const frameInterval = performanceMode ? 50 : 33; // ~20fps or ~30fps
        if (time - lastFrameTimeRef.current >= frameInterval) {
            captureAndSend();
            lastFrameTimeRef.current = time;
        }
        requestRef.current = requestAnimationFrame(animate);
    };

    const captureAndSend = () => {
        if (isWaitingRef.current || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        if (!videoRef.current || videoRef.current.readyState !== 4) return;

        const canvas = captureCanvasRef.current;
        const video = videoRef.current;
        if (!canvas) return;

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
                isWaitingRef.current = true;
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
        <Box sx={{ position: 'relative', width: '100%', height: '100%', bgcolor: '#000', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <Box sx={{ height: 32, bgcolor: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'space-between', px: 1.5, borderBottom: `1px solid ${theme.palette.divider}` }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: isConnected ? theme.palette.success.main : theme.palette.error.main, boxShadow: isConnected ? `0 0 8px ${theme.palette.success.main}` : 'none' }} />
                    <Typography variant="caption" sx={{ color: theme.palette.text.primary, fontWeight: 700 }}>
                        {isConnected ? 'LIVE FEED [ACTIVE]' : 'CONNECTING...'}
                    </Typography>
                </Box>
                <FormControl variant="standard">
                    <Select value={selectedDeviceId} onChange={(e) => setSelectedDeviceId(e.target.value)} disableUnderline sx={{ fontSize: '0.75rem', height: 24 }}>
                        {devices.map((d, i) => <MenuItem key={i} value={d.deviceId}>{d.label.slice(0, 20)}</MenuItem>)}
                    </Select>
                </FormControl>
            </Box>

            <Box sx={{ flexGrow: 1, position: 'relative', bgcolor: '#000', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <video ref={videoRef} hidden playsInline muted />
                <canvas ref={captureCanvasRef} style={{ display: 'none' }} />
                <canvas ref={displayCanvasRef} style={{ width: '100%', height: '100%', objectFit: 'contain' }} />

                {!isConnected && (
                    <Box sx={{ position: 'absolute', textAlign: 'center', color: '#fff' }}>
                        <RefreshCw size={24} className="spin" style={{ animation: 'spin 2s linear infinite' }} />
                        <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>INITIALIZING AI...</Typography>
                    </Box>
                )}


                <Box sx={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 72, background: `linear-gradient(to top, ${alpha(getRiskColor(currentScore), 0.9)} 0%, ${alpha(getRiskColor(currentScore), 0.4)} 100%)`, backdropFilter: 'blur(16px)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', px: 4 }}>
                    <Box sx={{ display: 'flex', gap: 4 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}><User size={18} color="#fff" /><Typography variant="h6" sx={{ color: '#fff', fontWeight: 900, fontFamily: 'monospace' }}>{metadata?.detections?.person_count || 0}</Typography></Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}><BoxIcon size={18} color="#fff" /><Typography variant="h6" sx={{ color: '#fff', fontWeight: 900, fontFamily: 'monospace' }}>{metadata?.detections?.object_count || 0}</Typography></Box>
                    </Box>
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'absolute', left: '50%', transform: 'translateX(-50%)' }}>
                        <Typography variant="overline" sx={{ color: 'rgba(255,255,255,0.7)', fontWeight: 800 }}>STATUS</Typography>
                        <Typography variant="h6" sx={{ color: '#fff', fontWeight: 900 }}>{(currentScore >= 75) ? 'CRITICAL BREACH' : (currentScore >= 50) ? 'ELEVATED RISK' : (currentScore >= 25) ? 'CAUTION REQ' : 'SECURE'}</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, bgcolor: 'rgba(255,255,255,0.15)', px: 2, py: 0.5, borderRadius: 2 }}>
                        <Typography variant="overline" sx={{ color: 'rgba(255,255,255,0.8)', fontWeight: 900 }}>THREAT</Typography>
                        <Typography variant="h3" sx={{ color: '#fff', fontWeight: 900, fontFamily: 'monospace', fontSize: '2rem' }}>{Math.round(currentScore)}%</Typography>
                    </Box>
                </Box>
            </Box>
            <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
        </Box>
    );
};

export default LiveFeed;
