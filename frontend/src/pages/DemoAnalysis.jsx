import React, { useState } from 'react';
import { Box, Typography, Button, Paper, Grid, LinearProgress, List, ListItem, ListItemText, Chip, ListItemIcon } from '@mui/material';
import { Upload, FileVideo, Play, AlertTriangle, CheckCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const DemoAnalysis = () => {
    const [file, setFile] = useState(null);
    const [processing, setProcessing] = useState(false);
    const [progress, setProgress] = useState(0);
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);

    const handleFileChange = (event) => {
        if (event.target.files && event.target.files[0]) {
            setFile(event.target.files[0]);
            setResults(null);
            setError(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setProcessing(true);
        setProgress(0);

        const formData = new FormData();
        formData.append('file', file);

        // Simulate progress
        const timer = setInterval(() => {
            setProgress((oldProgress) => {
                if (oldProgress === 100) {
                    return 100;
                }
                const diff = Math.random() * 10;
                return Math.min(oldProgress + diff, 90);
            });
        }, 500);

        try {
            const response = await fetch('http://localhost:8000/process/video', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error('Analysis failed');

            const data = await response.json();
            clearInterval(timer);
            setProgress(100);
            setTimeout(() => {
                setResults(data);
                setProcessing(false);
            }, 500);

        } catch (err) {
            console.error(err);
            setError('Error processing video. Please try again.');
            setProcessing(false);
            clearInterval(timer);
        }
    };

    return (
        <Box>
            <Typography variant="h5" color="text.primary" sx={{ mb: 3, letterSpacing: '0.05em' }}>
                AI VIDEO ANALYSIS DEMO
            </Typography>

            <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 4, textAlign: 'center', height: '100%', border: '1px dashed rgba(0, 243, 255, 0.3)' }}>
                        <input
                            accept="video/*"
                            style={{ display: 'none' }}
                            id="raised-button-file"
                            type="file"
                            onChange={handleFileChange}
                        />
                        <label htmlFor="raised-button-file">
                            <Box
                                sx={{
                                    p: 5,
                                    border: '1px dashed rgba(0, 243, 255, 0.2)',
                                    borderRadius: 2,
                                    cursor: 'pointer',
                                    transition: 'all 0.3s',
                                    '&:hover': { bgcolor: 'rgba(0, 243, 255, 0.05)', borderColor: 'primary.main' }
                                }}
                            >
                                <Upload size={48} color="#00f3ff" style={{ opacity: 0.7 }} />
                                <Typography variant="h6" sx={{ mt: 2 }}>
                                    {file ? file.name : "Drop video or Click to Upload"}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Support for MP4, AVI, MKV
                                </Typography>
                            </Box>
                        </label>

                        {file && (
                            <Button
                                variant="contained"
                                color="primary"
                                startIcon={<Play />}
                                onClick={handleUpload}
                                disabled={processing}
                                sx={{ mt: 3, width: '100%', py: 1.5 }}
                            >
                                {processing ? 'ANALYZING...' : 'START ANALYSIS'}
                            </Button>
                        )}

                        {processing && (
                            <Box sx={{ mt: 3, width: '100%' }}>
                                <LinearProgress variant="determinate" value={progress} />
                                <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                                    Processing frames with AI models...
                                </Typography>
                            </Box>
                        )}
                        {error && (
                            <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>
                        )}
                    </Paper>
                </Grid>

                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3, height: '100%', minHeight: 400 }}>
                        <Typography variant="h6" color="secondary" sx={{ mb: 2 }}>
                            ANALYSIS RESULTS
                        </Typography>

                        {!results && !processing && (
                            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '80%', opacity: 0.5 }}>
                                <FileVideo size={64} />
                                <Typography sx={{ mt: 2 }}>No results yet</Typography>
                            </Box>
                        )}

                        <AnimatePresence>
                            {results && (
                                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                                    <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
                                        <Paper sx={{ p: 2, flex: 1, bgcolor: 'rgba(255,0,0,0.1)', border: '1px solid rgba(255,0,0,0.3)' }}>
                                            <Typography variant="caption" color="error">ALERTS FOUND</Typography>
                                            <Typography variant="h4">{results.alerts_found}</Typography>
                                        </Paper>
                                        <Paper sx={{ p: 2, flex: 1, bgcolor: 'rgba(0,255,0,0.1)', border: '1px solid rgba(0,255,0,0.3)' }}>
                                            <Typography variant="caption" color="success">STATUS</Typography>
                                            <Typography variant="h6" color="success">COMPLETED</Typography>
                                        </Paper>
                                    </Box>

                                    <Typography variant="subtitle2" sx={{ mb: 1 }}>TIMELINE</Typography>
                                    <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                                        {results.alerts.map((alert, idx) => (
                                            <ListItem key={idx} sx={{
                                                mb: 1,
                                                bgcolor: 'rgba(255,255,255,0.02)',
                                                borderRadius: 1,
                                                borderLeft: `4px solid ${alert.level === 'CRITICAL' ? '#ff0055' : '#ff9900'}`
                                            }}>
                                                <ListItemIcon sx={{ minWidth: 40 }}>
                                                    <AlertTriangle size={20} color={alert.level === 'CRITICAL' ? '#ff0055' : '#ff9900'} />
                                                </ListItemIcon>
                                                <ListItemText
                                                    primary={
                                                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                                            <Typography variant="body2">{alert.level} RISK DETECTED</Typography>
                                                            <Chip size="small" label={`Score: ${alert.score.toFixed(1)}`} color={alert.level === 'CRITICAL' ? 'error' : 'warning'} />
                                                        </Box>
                                                    }
                                                    secondary={`Frame: ${alert.frame_number} | Time: ${alert.timestamp_seconds.toFixed(2)}s`}
                                                />
                                            </ListItem>
                                        ))}
                                        {results.alerts.length === 0 && (
                                            <ListItem>
                                                <ListItemIcon><CheckCircle color="#00ff00" /></ListItemIcon>
                                                <ListItemText primary="No threats detected in this footage." />
                                            </ListItem>
                                        )}
                                    </List>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};

export default DemoAnalysis;
