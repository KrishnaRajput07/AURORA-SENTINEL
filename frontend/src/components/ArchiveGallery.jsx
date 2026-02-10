import React, { useState, useEffect } from 'react';
import { Box, Typography, Grid, Card, CardContent, CardMedia, IconButton, Tab, Tabs, alpha, useTheme, Button, CircularProgress, Dialog } from '@mui/material';
import { Play, Trash2, Download, FileVideo, Clock, RefreshCw, HardDrive, X } from 'lucide-react';
import { format } from 'date-fns';

const ArchiveGallery = () => {
    const [clips, setClips] = useState([]);
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState('active');
    const [selectedClip, setSelectedClip] = useState(null);
    const theme = useTheme();

    useEffect(() => {
        fetchClips();
    }, [tab]);

    const fetchClips = async () => {
        setLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/archive/list?source=${tab}`);
            const data = await response.json();
            setClips(data.clips || []);
        } catch (error) {
            console.error('Error fetching clips:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = (clip) => {
        const link = document.createElement('a');
        link.href = `http://localhost:8000${clip.url}`;
        link.download = clip.name;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const getFormattedSize = (bytes) => {
        if (!bytes) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    return (
        <Box sx={{ p: 0 }}>
            <Box sx={{
                borderBottom: `1px solid ${theme.palette.divider}`,
                px: 3,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                bgcolor: alpha('#F8FAFC', 0.5)
            }}>
                <Tabs value={tab} onChange={(e, v) => setTab(v)} sx={{ minHeight: 64 }}>
                    <Tab
                        label="Active Alerts"
                        value="active"
                        icon={<HardDrive size={18} />}
                        iconPosition="start"
                        sx={{ fontWeight: 700, fontSize: '0.85rem' }}
                    />
                    <Tab
                        label="Smart Bin"
                        value="bin"
                        icon={<Trash2 size={18} />}
                        iconPosition="start"
                        sx={{ fontWeight: 700, fontSize: '0.85rem' }}
                    />
                </Tabs>
                <IconButton onClick={fetchClips} size="small" disabled={loading}>
                    <RefreshCw size={18} className={loading ? 'spin' : ''} />
                </IconButton>
            </Box>

            <Box sx={{ p: 3, maxHeight: 600, overflowY: 'auto' }}>
                {loading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 8 }}>
                        <CircularProgress size={32} />
                    </Box>
                ) : clips.length === 0 ? (
                    <Box sx={{ textAlign: 'center', py: 8, opacity: 0.5 }}>
                        <FileVideo size={48} strokeWidth={1} style={{ marginBottom: 16 }} />
                        <Typography variant="body1" sx={{ fontWeight: 600 }}>No clips found in {tab} storage</Typography>
                        <Typography variant="caption">Clips are automatically archived when threat levels exceed 70%</Typography>
                    </Box>
                ) : (
                    <Grid container spacing={2}>
                        {clips.map((clip) => (
                            <Grid item xs={12} sm={6} md={4} key={clip.id}>
                                <Card sx={{
                                    bgcolor: '#fff',
                                    border: `1px solid ${theme.palette.divider}`,
                                    boxShadow: 'none',
                                    borderRadius: 3,
                                    overflow: 'hidden',
                                    transition: 'all 0.3s ease',
                                    '&:hover': {
                                        transform: 'translateY(-4px)',
                                        boxShadow: '0 12px 24px rgba(0,0,0,0.05)',
                                        borderColor: theme.palette.primary.main
                                    }
                                }}>
                                    <Box sx={{ position: 'relative', height: 140, bgcolor: '#000', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <FileVideo size={32} color={alpha('#fff', 0.2)} />
                                        <Box sx={{
                                            position: 'absolute',
                                            bottom: 8,
                                            right: 8,
                                            px: 1,
                                            py: 0.25,
                                            bgcolor: 'rgba(0,0,0,0.6)',
                                            borderRadius: 1,
                                            color: '#fff',
                                            fontSize: '0.65rem',
                                            fontWeight: 800
                                        }}>
                                            MP4
                                        </Box>
                                    </Box>
                                    <CardContent sx={{ p: 2 }}>
                                        <Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 0.5, noWrap: true, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                            {clip.name}
                                        </Typography>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, opacity: 0.6 }}>
                                                <Clock size={12} />
                                                <Typography variant="caption" sx={{ fontWeight: 600 }}>
                                                    {format(new Date(clip.created_at), 'MMM d, HH:mm')}
                                                </Typography>
                                            </Box>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, opacity: 0.6 }}>
                                                <HardDrive size={12} />
                                                <Typography variant="caption" sx={{ fontWeight: 600 }}>
                                                    {getFormattedSize(clip.size)}
                                                </Typography>
                                            </Box>
                                        </Box>
                                        <Box sx={{ display: 'flex', gap: 1 }}>
                                            <Button
                                                fullWidth
                                                variant="contained"
                                                size="small"
                                                startIcon={<Play size={14} />}
                                                onClick={() => setSelectedClip(clip)}
                                                sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 700 }}
                                            >
                                                View
                                            </Button>
                                            <IconButton
                                                size="small"
                                                onClick={() => handleDownload(clip)}
                                                sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 2 }}
                                            >
                                                <Download size={14} />
                                            </IconButton>
                                        </Box>
                                    </CardContent>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                )}
            </Box>
            {/* Video Player Dialog */}
            <Dialog
                open={!!selectedClip}
                onClose={() => setSelectedClip(null)}
                maxWidth="md"
                fullWidth
                PaperProps={{ sx: { bgcolor: '#000', borderRadius: 4, overflow: 'hidden' } }}
            >
                <Box sx={{ position: 'relative', pt: '56.25%', bgcolor: '#000' }}>
                    {selectedClip && (
                        <video
                            src={`http://localhost:8000${selectedClip.url}`}
                            controls
                            autoPlay
                            style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}
                        />
                    )}
                    <IconButton
                        onClick={() => setSelectedClip(null)}
                        sx={{ position: 'absolute', top: 12, right: 12, color: '#fff', bgcolor: 'rgba(0,0,0,0.5)', '&:hover': { bgcolor: 'rgba(0,0,0,0.7)' } }}
                    >
                        <X size={20} />
                    </IconButton>
                </Box>
                <Box sx={{ p: 2, bgcolor: '#111', borderTop: '1px solid #333' }}>
                    <Typography variant="subtitle1" sx={{ color: '#fff', fontWeight: 800 }}>
                        {selectedClip?.name}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)' }}>
                        Archived: {selectedClip && format(new Date(selectedClip.created_at), 'PPPP p')}
                    </Typography>
                </Box>
            </Dialog>
        </Box>
    );
};

export default ArchiveGallery;
