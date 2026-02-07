import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Box, Typography, Paper, Grid, Button, IconButton, LinearProgress, Drawer, List, ListItem, alpha, useTheme, Chip, Divider, CircularProgress } from '@mui/material';
import { Upload, FileVideo, X, Play, Shield, Search, ChevronRight, AlertTriangle, CheckCircle2, Clock, Activity, Users, Target, Rewind, Maximize2 } from 'lucide-react';
import { useDropzone } from 'react-dropzone';

const Intelligence = () => {
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [drawerOpen, setDrawerOpen] = useState(false);
    const [activeTab, setActiveTab] = useState('summary');
    const videoRef = useRef(null);
    const theme = useTheme();

    const onDrop = useCallback(acceptedFiles => {
        setFile(acceptedFiles[0]);
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'video/*': ['.mp4', '.mov', '.avi'] },
        multiple: false,
        disabled: uploading
    });

    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);
        setProgress(5);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const timer = setInterval(() => {
                setProgress(prev => (prev < 90 ? prev + 3 : prev));
            }, 1000);

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
        }
    };

    return (
        <Box sx={{ maxWidth: 1600, mx: 'auto', p: { xs: 2, md: 4 } }}>
            {/* Header */}
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                <Box>
                    <Typography variant="h3" sx={{ fontWeight: 900, letterSpacing: '-0.04em', color: theme.palette.text.primary, mb: 1, display: 'flex', alignItems: 'center', gap: 2 }}>
                        Intelligence <Box sx={{ px: 1.5, py: 0.5, bgcolor: theme.palette.primary.main, color: '#fff', borderRadius: 2, fontSize: '0.9rem', fontWeight: 900 }}>v2.0 PRO</Box>
                    </Typography>
                    <Typography variant="body1" sx={{ color: theme.palette.text.secondary, fontWeight: 500 }}>
                        Forensic AI pipeline with pose estimation and behavioral tracking.
                    </Typography>
                </Box>
                {analysisResult && (
                    <Button variant="outlined" onClick={() => setDrawerOpen(true)} startIcon={<Activity size={18} />} sx={{ borderRadius: 2, fontWeight: 700 }}>
                        Open Forensic Player
                    </Button>
                )}
            </Box>

            <Grid container spacing={4}>
                {/* LEFT COLUMN: Upload & Analysis Results */}
                <Grid item xs={12} lg={analysisResult ? 12 : 8}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        {/* Upload Section */}
                        <Paper
                            {...getRootProps()}
                            sx={{
                                p: 6,
                                textAlign: 'center',
                                cursor: uploading ? 'not-allowed' : 'pointer',
                                border: `2px dashed ${isDragActive ? theme.palette.primary.main : alpha(theme.palette.divider, 0.5)}`,
                                borderRadius: 6,
                                bgcolor: isDragActive ? alpha(theme.palette.primary.main, 0.05) : '#fff',
                                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                boxShadow: isDragActive ? '0 20px 40px rgba(0,0,0,0.05)' : 'none',
                                '&:hover': { borderColor: theme.palette.primary.main, bgcolor: alpha(theme.palette.primary.main, 0.01) }
                            }}
                        >
                            <input {...getInputProps()} />
                            <Box sx={{ mb: 3, display: 'inline-flex', p: 4, borderRadius: '50%', bgcolor: alpha(theme.palette.primary.main, 0.1) }}>
                                {uploading ? <CircularProgress size={48} thickness={4} /> : <Upload size={48} color={theme.palette.primary.main} />}
                            </Box>
                            <Typography variant="h5" sx={{ fontWeight: 800, mb: 1 }}>
                                {file ? file.name : 'Ingest Forensics Data'}
                            </Typography>
                            <Typography variant="body2" sx={{ color: theme.palette.text.secondary, mb: 4, maxWidth: 300, mx: 'auto' }}>
                                Drag and drop surveillance footage for multi-model AI processing.
                            </Typography>

                            {file && !uploading && !analysisResult && (
                                <Button
                                    variant="contained" size="large"
                                    onClick={(e) => { e.stopPropagation(); handleUpload(); }}
                                    sx={{ borderRadius: 3, px: 8, py: 2, fontWeight: 900, textTransform: 'none', fontSize: '1.1rem', boxShadow: '0 10px 20px rgba(0,0,0,0.1)' }}
                                >
                                    Initialize AI Analysis
                                </Button>
                            )}

                            {uploading && (
                                <Box sx={{ width: '100%', mt: 2, maxWidth: 400, mx: 'auto' }}>
                                    <Typography variant="caption" sx={{ fontWeight: 900, mb: 1.5, display: 'block', color: theme.palette.primary.main, letterSpacing: '0.1em' }}>
                                        EXTRACTING KEYPOINTS & SKELETONS... {progress}%
                                    </Typography>
                                    <LinearProgress variant="determinate" value={progress} sx={{ height: 10, borderRadius: 5, bgcolor: alpha(theme.palette.primary.main, 0.1) }} />
                                </Box>
                            )}

                            {analysisResult && (
                                <Button variant="text" color="primary" onClick={() => { setAnalysisResult(null); setFile(null); }} sx={{ fontWeight: 800 }}>
                                    Upload New Footage
                                </Button>
                            )}
                        </Paper>

                        {/* Analysis Results (Displayed below upload when ready) */}
                        {analysisResult && (
                            <Box sx={{ animation: 'fadeInUp 0.6s ease-out' }}>
                                <Typography variant="h5" sx={{ fontWeight: 900, mb: 3, display: 'flex', alignItems: 'center', gap: 1.5 }}>
                                    <Target size={24} color={theme.palette.primary.main} /> Analysis Summary
                                </Typography>

                                <Grid container spacing={3}>
                                    {/* Score Card */}
                                    <Grid item xs={12} md={4}>
                                        <Paper sx={{ p: 3, borderRadius: 5, bgcolor: alpha(theme.palette.error.main, 0.03), border: `1px solid ${alpha(theme.palette.error.main, 0.1)}` }}>
                                            <Typography variant="caption" sx={{ fontWeight: 900, opacity: 0.6, letterSpacing: '0.1em' }}>FIGHT PROBABILITY</Typography>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
                                                <Typography variant="h2" sx={{ fontWeight: 900, color: theme.palette.error.main }}>
                                                    {analysisResult.metrics.fight_probability}%
                                                </Typography>
                                                <AlertTriangle size={32} color={theme.palette.error.main} />
                                            </Box>
                                        </Paper>
                                    </Grid>

                                    {/* Metrics Grid */}
                                    <Grid item xs={12} md={8}>
                                        <Grid container spacing={2}>
                                            <Grid item xs={6} sm={4}>
                                                <Paper sx={{ p: 2, borderRadius: 4, textAlign: 'center' }}>
                                                    <Users size={20} style={{ marginBottom: 8, opacity: 0.5 }} />
                                                    <Typography variant="h5" sx={{ fontWeight: 900 }}>{analysisResult.metrics.max_persons}</Typography>
                                                    <Typography variant="caption" sx={{ fontWeight: 700, opacity: 0.5 }}>PEAK CAPACITY</Typography>
                                                </Paper>
                                            </Grid>
                                            <Grid item xs={6} sm={4}>
                                                <Paper sx={{ p: 2, borderRadius: 4, textAlign: 'center' }}>
                                                    <Activity size={20} style={{ marginBottom: 8, opacity: 0.5 }} />
                                                    <Typography variant="h5" sx={{ fontWeight: 900 }}>POSE</Typography>
                                                    <Typography variant="caption" sx={{ fontWeight: 700, opacity: 0.5 }}>ACTIVE SCAN</Typography>
                                                </Paper>
                                            </Grid>
                                            <Grid item xs={12} sm={4}>
                                                <Paper sx={{ p: 2, borderRadius: 4, textAlign: 'center', bgcolor: theme.palette.success.main, color: '#fff' }}>
                                                    <CheckCircle2 size={20} style={{ marginBottom: 8 }} />
                                                    <Typography variant="h5" sx={{ fontWeight: 900 }}>SECURE</Typography>
                                                    <Typography variant="caption" sx={{ fontWeight: 700, opacity: 0.8 }}>SYSTEM STATUS</Typography>
                                                </Paper>
                                            </Grid>
                                        </Grid>
                                    </Grid>

                                    {/* Suspicious Patterns */}
                                    <Grid item xs={12}>
                                        <Paper sx={{ p: 3, borderRadius: 5 }}>
                                            <Typography variant="subtitle1" sx={{ fontWeight: 800, mb: 2 }}>Suspicious Motion Patterns</Typography>
                                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
                                                {analysisResult.metrics.suspicious_patterns.length > 0 ? (
                                                    analysisResult.metrics.suspicious_patterns.map((p, i) => (
                                                        <Chip key={i} label={p} variant="outlined" color="error" sx={{ fontWeight: 700, borderRadius: 2 }} />
                                                    ))
                                                ) : (
                                                    <Typography variant="body2" sx={{ opacity: 0.5 }}>No aggressive motion vectors detected.</Typography>
                                                )}
                                            </Box>
                                        </Paper>
                                    </Grid>

                                    {/* Event Markers List */}
                                    <Grid item xs={12}>
                                        <Paper sx={{ p: 3, borderRadius: 5 }}>
                                            <Typography variant="subtitle1" sx={{ fontWeight: 800, mb: 2 }}>Detailed Event Markers</Typography>
                                            <List disablePadding>
                                                {analysisResult.alerts.map((alert, i) => (
                                                    <ListItem key={i} button onClick={() => { setDrawerOpen(true); setTimeout(() => seekTo(alert.timestamp_seconds), 100); }}
                                                        sx={{ px: 2, py: 1.5, mb: 1, borderRadius: 3, bgcolor: alpha(theme.palette.error.main, 0.05), border: `1px solid ${alpha(theme.palette.error.main, 0.1)}` }}>
                                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                                                            <Box sx={{ display: 'flex', gap: 3, alignItems: 'center' }}>
                                                                <Typography sx={{ fontWeight: 900, color: theme.palette.error.main, minWidth: 60 }}>
                                                                    {Math.floor(alert.timestamp_seconds / 60)}:{(alert.timestamp_seconds % 60).toFixed(0).padStart(2, '0')}s
                                                                </Typography>
                                                                <Box>
                                                                    <Typography variant="subtitle2" sx={{ fontWeight: 800 }}>{alert.level} RISK DETECTED</Typography>
                                                                    <Typography variant="caption">Contributing: {alert.top_factors.map(f => f.name).join(', ')}</Typography>
                                                                </Box>
                                                            </Box>
                                                            <ChevronRight size={20} />
                                                        </Box>
                                                    </ListItem>
                                                ))}
                                            </List>
                                        </Paper>
                                    </Grid>
                                </Grid>
                            </Box>
                        )}
                    </Box>
                </Grid>
            </Grid>

            {/* COLLAPSIBLE PRO DRAWER (RIGHT SIDE) */}
            <Drawer
                anchor="right"
                open={drawerOpen}
                onClose={() => setDrawerOpen(false)}
                PaperProps={{ sx: { width: { xs: '100%', sm: 600, md: 800 }, p: 0, bgcolor: '#000', borderLeft: '1px solid #333' } }}
            >
                <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', color: '#fff' }}>
                    {/* Drawer Header */}
                    <Box sx={{ p: 3, borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center', bgcolor: '#111' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <IconButton onClick={() => setDrawerOpen(false)} size="small" sx={{ color: '#fff', bgcolor: 'rgba(255,255,255,0.1)' }}>
                                <X size={20} />
                            </IconButton>
                            <Typography variant="h6" sx={{ fontWeight: 900 }}>PRO FORENSIC PLAYER</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                            <Chip label="AI RENDERING" size="small" sx={{ bgcolor: alpha(theme.palette.primary.main, 0.2), color: theme.palette.primary.main, fontWeight: 900 }} />
                        </Box>
                    </Box>

                    {/* Pro Video Player Section */}
                    <Box sx={{ flexGrow: 1, p: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>
                        <Box sx={{ position: 'relative', bgcolor: '#000', borderRadius: 4, overflow: 'hidden', boxShadow: '0 30px 60px rgba(0,0,0,0.5)', border: '1px solid #333', minHeight: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <video
                                ref={videoRef}
                                src={analysisResult?.processed_url ? `http://localhost:8000${analysisResult.processed_url}` : null}
                                controls
                                style={{ width: '100%', maxHeight: '70vh', display: analysisResult?.processed_url ? 'block' : 'none' }}
                                onError={(e) => {
                                    console.error("Video Error:", e);
                                    // Fallback to original file or show error
                                }}
                            />
                            {!analysisResult?.processed_url && (
                                <Box sx={{ textAlign: 'center', p: 4 }}>
                                    <CircularProgress color="primary" />
                                    <Typography sx={{ mt: 2, color: 'rgba(255,255,255,0.5)' }}>Loading Forensic Stream...</Typography>
                                </Box>
                            )}
                            <Box sx={{ position: 'absolute', top: 20, left: 20, pointerEvents: 'none', display: 'flex', gap: 1 }}>
                                <Chip label="AI RENDERING" size="small" color="error" sx={{ fontWeight: 900, borderRadius: 1 }} />
                                <Chip label="H.264" size="small" sx={{ bgcolor: 'rgba(255,255,255,0.1)', color: '#fff', fontWeight: 900, borderRadius: 1 }} />
                            </Box>
                        </Box>

                        {/* Player Controls (Custom labels for better UX) */}
                        <Box sx={{ p: 3, bgcolor: '#111', borderRadius: 4, border: '1px solid #333' }}>
                            <Grid container spacing={2}>
                                <Grid item xs={12}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography variant="caption" sx={{ fontWeight: 900, opacity: 0.6 }}>AI METADATA STREAM</Typography>
                                        <Typography variant="caption" sx={{ fontWeight: 900, color: theme.palette.primary.main }}>ACTIVE</Typography>
                                    </Box>
                                    <LinearProgress variant="determinate" value={45} sx={{ height: 4, borderRadius: 2, bgcolor: '#222' }} />
                                </Grid>
                                <Grid item xs={12} sx={{ display: 'flex', gap: 2 }}>
                                    <Button variant="outlined" startIcon={<Rewind size={18} />} onClick={() => videoRef.current.currentTime -= 5} sx={{ color: '#fff', borderColor: '#333', textTransform: 'none', fontWeight: 700 }}>Rewind 5s</Button>
                                    <Button variant="outlined" startIcon={<Clock size={18} />} sx={{ color: '#fff', borderColor: '#333', textTransform: 'none', fontWeight: 700 }}>Jump to Start</Button>
                                    <IconButton sx={{ ml: 'auto', color: '#fff' }}><Maximize2 size={18} /></IconButton>
                                </Grid>
                            </Grid>
                        </Box>

                        <Divider sx={{ borderColor: '#333' }} />

                        {/* Analysis Feed in Drawer */}
                        <Box sx={{ flexGrow: 1, overflowY: 'auto' }}>
                            <Typography variant="subtitle2" sx={{ fontWeight: 900, mb: 2, letterSpacing: '0.1em', opacity: 0.5 }}>FORENSIC TIMELINE</Typography>
                            <List disablePadding>
                                {analysisResult?.alerts.map((alert, i) => (
                                    <ListItem key={i} button onClick={() => seekTo(alert.timestamp_seconds)}
                                        sx={{ px: 2, py: 2, mb: 1.5, borderRadius: 3, bgcolor: '#111', border: '1px solid #222', '&:hover': { bgcolor: '#1a1a1a' } }}>
                                        <Box sx={{ display: 'flex', gap: 2, width: '100%' }}>
                                            <Typography sx={{ fontWeight: 900, color: theme.palette.primary.main }}>{alert.timestamp_seconds.toFixed(1)}s</Typography>
                                            <Box>
                                                <Typography variant="body2" sx={{ fontWeight: 800 }}>{alert.level} RISK EVENT</Typography>
                                                <Typography variant="caption" sx={{ opacity: 0.6 }}>Confidence: {alert.score}% | Factors: {alert.top_factors.map(f => f.name).join(', ')}</Typography>
                                            </Box>
                                        </Box>
                                    </ListItem>
                                ))}
                            </List>
                        </Box>
                    </Box>

                    {/* Footer Action */}
                    <Box sx={{ p: 3, borderTop: '1px solid #333', bgcolor: '#111' }}>
                        <Button fullWidth variant="contained" size="large" sx={{ py: 2, borderRadius: 3, fontWeight: 900, textTransform: 'none' }}>
                            Generate Forensic PDF Report
                        </Button>
                    </Box>
                </Box>
            </Drawer>

            <style>
                {`
                    @keyframes fadeInUp {
                        from { opacity: 0; transform: translateY(20px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                `}
            </style>
        </Box>
    );
};

export default Intelligence;
