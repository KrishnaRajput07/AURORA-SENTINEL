import React, { useState, useCallback, useRef } from 'react';
import { Box, Typography, Paper, Grid, Button, IconButton, LinearProgress, Drawer, List, ListItem, alpha, useTheme, Chip } from '@mui/material';
import { Upload, FileVideo, X, Play, Shield, Search, ChevronRight, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useDropzone } from 'react-dropzone';

const Intelligence = () => {
    const [file, setFile] = useState(null);
    const [videoUrl, setVideoUrl] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [drawerOpen, setDrawerOpen] = useState(false);
    const videoRef = useRef(null);
    const theme = useTheme();

    const onDrop = useCallback(acceptedFiles => {
        const selectedFile = acceptedFiles[0];
        setFile(selectedFile);
        setVideoUrl(URL.createObjectURL(selectedFile));
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'video/*': ['.mp4', '.mov', '.avi'] },
        multiple: false
    });

    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);
        setProgress(10);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const timer = setInterval(() => {
                setProgress(prev => {
                    if (prev >= 95) { clearInterval(timer); return 95; }
                    return prev + 5;
                });
            }, 800);

            const response = await fetch('http://localhost:8000/process/video', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            clearInterval(timer);
            setAnalysisResult(data);
            setDrawerOpen(true);
        } catch (error) {
            console.error('Upload failed:', error);
        } finally {
            setUploading(false);
            setProgress(0);
        }
    };

    const seekTo = (seconds) => {
        if (videoRef.current) {
            videoRef.current.currentTime = seconds;
            videoRef.current.play();
            setDrawerOpen(true); // Close drawer to see video? No, keep open but jump.
        }
    };

    return (
        <Box>
            <Box sx={{ mb: 4 }}>
                <Typography variant="h4" sx={{ fontWeight: 900, letterSpacing: '-0.02em', color: theme.palette.text.primary, mb: 1 }}>
                    Intelligence Center
                </Typography>
                <Typography variant="body1" sx={{ color: theme.palette.text.secondary }}>
                    Upload surveillance footage for deep forensic analysis and threat identification.
                </Typography>
            </Box>

            {!analysisResult ? (
                <Grid container spacing={3}>
                    <Grid item xs={12} lg={8}>
                        <Paper
                            {...getRootProps()}
                            sx={{
                                p: 8,
                                textAlign: 'center',
                                cursor: 'pointer',
                                border: `2px dashed ${isDragActive ? theme.palette.primary.main : alpha(theme.palette.divider, 0.5)}`,
                                borderRadius: 4,
                                bgcolor: isDragActive ? alpha(theme.palette.primary.main, 0.05) : 'transparent',
                                transition: 'all 0.3s ease',
                                '&:hover': {
                                    bgcolor: alpha(theme.palette.primary.main, 0.02),
                                    borderColor: theme.palette.primary.main
                                }
                            }}
                        >
                            <input {...getInputProps()} />
                            <Box sx={{ mb: 3, display: 'inline-flex', p: 3, borderRadius: '50%', bgcolor: alpha(theme.palette.primary.main, 0.1) }}>
                                <Upload size={48} color={theme.palette.primary.main} />
                            </Box>
                            <Typography variant="h5" sx={{ fontWeight: 800, mb: 1 }}>
                                {file ? file.name : 'Drag & drop security footage'}
                            </Typography>
                            <Typography variant="body2" sx={{ color: theme.palette.text.secondary, mb: 4 }}>
                                Supports MP4, AVI, and MOV files up to 500MB
                            </Typography>
                            {file && !uploading && (
                                <Button
                                    variant="contained"
                                    size="large"
                                    onClick={(e) => { e.stopPropagation(); handleUpload(); }}
                                    sx={{ borderRadius: 3, px: 6, fontWeight: 700, textTransform: 'none' }}
                                >
                                    Start Deep Analysis
                                </Button>
                            )}
                            {uploading && (
                                <Box sx={{ width: '100%', mt: 2 }}>
                                    <Typography variant="caption" sx={{ fontWeight: 800, mb: 1, display: 'block', color: theme.palette.primary.main }}>
                                        AI FORENSIC SCANNING... {progress}%
                                    </Typography>
                                    <LinearProgress variant="determinate" value={progress} sx={{ height: 8, borderRadius: 4, bgcolor: alpha(theme.palette.primary.main, 0.1) }} />
                                </Box>
                            )}
                        </Paper>
                    </Grid>

                    <Grid item xs={12} lg={4}>
                        <Paper sx={{ p: 3, borderRadius: 4, height: '100%', border: `1px solid ${theme.palette.divider}` }}>
                            <Typography variant="subtitle1" sx={{ fontWeight: 800, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Shield size={18} color={theme.palette.primary.main} /> Recent Activity
                            </Typography>
                            <List disablePadding>
                                {[1, 2, 3].map(i => (
                                    <ListItem key={i} sx={{ px: 0, py: 1.5, borderBottom: i < 3 ? `1px solid ${theme.palette.divider}` : 'none' }}>
                                        <Box sx={{ display: 'flex', gap: 2, width: '100%' }}>
                                            <Box sx={{ width: 48, height: 48, borderRadius: 2, bgcolor: alpha('#000', 0.1), display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                                <FileVideo size={20} opacity={0.5} />
                                            </Box>
                                            <Box sx={{ flexGrow: 1 }}>
                                                <Typography variant="subtitle2" sx={{ fontWeight: 700, lineHeight: 1.2 }}>Security_Cam_0{i}.mp4</Typography>
                                                <Typography variant="caption" sx={{ opacity: 0.6 }}>2.4 MB • 12m ago</Typography>
                                            </Box>
                                            <Chip label="Secure" size="small" variant="outlined" sx={{ fontWeight: 700, fontSize: '0.65rem' }} />
                                        </Box>
                                    </ListItem>
                                ))}
                            </List>
                            <Button fullWidth sx={{ mt: 2, textTransform: 'none', fontWeight: 700 }}>View Full History</Button>
                        </Paper>
                    </Grid>
                </Grid>
            ) : (
                <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Button startIcon={<Upload size={18} />} onClick={() => { setAnalysisResult(null); setFile(null); setVideoUrl(null); }}>Upload New</Button>
                            <Typography variant="h6" sx={{ fontWeight: 700 }}>Results for: {analysisResult.filename}</Typography>
                        </Box>
                        <Button variant="contained" onClick={() => setDrawerOpen(true)} startIcon={<Search size={18} />} sx={{ borderRadius: 2 }}>Open Analytics Drawer</Button>
                    </Box>

                    <Grid container spacing={3}>
                        <Grid item xs={12} md={8}>
                            <Paper sx={{ p: 2, borderRadius: 4, bgcolor: '#000', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
                                <video ref={videoRef} src={videoUrl} controls style={{ width: '100%', borderRadius: 8 }} />
                                <Box sx={{ position: 'absolute', top: 30, left: 30, px: 2, py: 0.5, bgcolor: 'rgba(255,0,0,0.8)', color: '#fff', borderRadius: 2, fontSize: '0.75rem', fontWeight: 900, pointerEvents: 'none' }}>
                                    AI ANALYSIS ACTIVE
                                </Box>
                            </Paper>
                        </Grid>
                        <Grid item xs={12} md={4}>
                            <Paper sx={{ p: 3, borderRadius: 4, height: '100%', maxHeight: 600, overflowY: 'auto', border: `1px solid ${theme.palette.divider}` }}>
                                <Typography variant="subtitle1" sx={{ fontWeight: 800, mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <Clock size={18} color={theme.palette.primary.main} /> Event Markers
                                </Typography>
                                <List disablePadding>
                                    {analysisResult.alerts.map((alert, i) => (
                                        <ListItem key={i} button onClick={() => seekTo(alert.timestamp_seconds)}
                                            sx={{ px: 2, py: 1.5, mb: 1.5, borderRadius: 3, bgcolor: alpha(theme.palette.error.main, 0.05), border: `1px solid ${alpha(theme.palette.error.main, 0.1)}`, '&:hover': { bgcolor: alpha(theme.palette.error.main, 0.1) } }}>
                                            <Box sx={{ display: 'flex', gap: 2, width: '100%' }}>
                                                <Typography sx={{ fontWeight: 900, color: theme.palette.error.main, minWidth: 50 }}>
                                                    {Math.floor(alert.timestamp_seconds / 60)}:{(alert.timestamp_seconds % 60).toFixed(0).padStart(2, '0')}
                                                </Typography>
                                                <Box sx={{ flexGrow: 1 }}>
                                                    <Typography variant="subtitle2" sx={{ fontWeight: 800 }}>{alert.level.toUpperCase()}</Typography>
                                                    <Typography variant="caption" sx={{ display: 'block', fontWeight: 600, opacity: 0.7 }}>{alert.top_factors.join(', ')}</Typography>
                                                </Box>
                                                <ChevronRight size={18} color={theme.palette.error.main} />
                                            </Box>
                                        </ListItem>
                                    ))}
                                    {analysisResult.alerts.length === 0 && (
                                        <Box sx={{ p: 4, textAlign: 'center', opacity: 0.5 }}>
                                            <CheckCircle2 size={32} style={{ marginBottom: 8 }} />
                                            <Typography variant="body2" sx={{ fontWeight: 700 }}>No security threats identified</Typography>
                                        </Box>
                                    )}
                                </List>
                            </Paper>
                        </Grid>
                    </Grid>
                </Box>
            )}

            <Drawer
                anchor="right"
                open={drawerOpen}
                onClose={() => setDrawerOpen(false)}
                PaperProps={{ sx: { width: { xs: '100%', sm: 500, md: 550 }, p: 0, bgcolor: '#FFFFFF' } }}
            >
                <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <Box sx={{ p: 3, borderBottom: `1px solid ${theme.palette.divider}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <IconButton onClick={() => setDrawerOpen(false)} size="small">
                                <X size={20} />
                            </IconButton>
                            <Typography variant="h6" sx={{ fontWeight: 800 }}>AI Forensic Log</Typography>
                        </Box>
                        {analysisResult && (
                            <Chip
                                label={analysisResult.alerts_found > 0 ? `${analysisResult.alerts_found} Threats Found` : "Footage Clear"}
                                color={analysisResult.alerts_found > 0 ? "error" : "success"}
                                sx={{ fontWeight: 800, borderRadius: 2 }}
                            />
                        )}
                    </Box>

                    <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 4 }}>
                        <Box sx={{ mb: 4, p: 3, bgcolor: alpha(theme.palette.primary.main, 0.05), borderRadius: 4 }}>
                            <Typography variant="caption" sx={{ fontWeight: 900, mb: 1, display: 'block', letterSpacing: '0.1em' }}>AI INTELLIGENCE SUMMARY</Typography>
                            <Typography variant="body2" sx={{ fontWeight: 600, opacity: 0.8, lineHeight: 1.6 }}>
                                Full scan complete for {analysisResult?.filename}. AI identified {analysisResult?.alerts_found} critical risk markers.
                                Peak risk escalation reached {Math.max(...(analysisResult?.alerts.map(a => a.score) || [0]))}%.
                            </Typography>
                        </Box>

                        <Typography variant="subtitle1" sx={{ fontWeight: 800, mb: 2 }}>Event Deep-Dive</Typography>
                        <List disablePadding>
                            {analysisResult?.alerts.map((alert, i) => (
                                <ListItem key={i} sx={{ px: 0, py: 2.5, borderBottom: `1px solid ${theme.palette.divider}`, display: 'block' }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
                                        <Typography variant="overline" sx={{ fontWeight: 900, color: theme.palette.error.main }}>TIMESTAMP: {alert.timestamp_seconds.toFixed(1)}s</Typography>
                                        <Typography variant="caption" sx={{ fontWeight: 800, bgcolor: alpha(theme.palette.error.main, 0.1), px: 1, py: 0.5, borderRadius: 1 }}>RISK: {alert.score}%</Typography>
                                    </Box>
                                    <Typography variant="body1" sx={{ fontWeight: 700, mb: 1 }}>{alert.level.toUpperCase() - alert.top_factors.join(' detected. ')}</Typography>
                                    <Button size="small" variant="contained" color="secondary" onClick={() => seekTo(alert.timestamp_seconds)} sx={{ textTransform: 'none', borderRadius: 2, fontWeight: 700 }}>
                                        Examine in Player
                                    </Button>
                                </ListItem>
                            ))}
                        </List>
                    </Box>

                    <Box sx={{ p: 3, borderTop: `1px solid ${theme.palette.divider}`, display: 'flex', gap: 2 }}>
                        <Button fullWidth variant="contained" size="large" sx={{ py: 2, borderRadius: 3, fontWeight: 700, textTransform: 'none', boxShadow: '0 8px 16px rgba(0,0,0,0.1)' }}>
                            Export Forensic Evidence
                        </Button>
                    </Box>
                </Box>
            </Drawer>
        </Box>
    );
};

export default Intelligence;
