import React, { useState, useEffect } from 'react';
import { Box, Typography, Grid, Card, CardContent, CardMedia, IconButton, Tab, Tabs, alpha, useTheme, Button, CircularProgress, Dialog, Chip } from '@mui/material';
import { Play, Trash2, Download, FileVideo, Clock, RefreshCw, HardDrive, X, AlertTriangle, MapPin, RefreshCcw as Refresh } from 'lucide-react';
import { format } from 'date-fns';
import { API_BASE_URL } from '../config';

// Helper function to safely parse API dates
const parseApiDate = (dateString) => {
    if (!dateString) return null;
    try {
        return new Date(dateString);
    } catch (error) {
        console.warn('Invalid date string:', dateString);
        return null;
    }
};

// Helper function to safely format dates
const safeFormat = (date, formatStr) => {
    if (!date) return 'Invalid Date';
    try {
        return format(date, formatStr);
    } catch (error) {
        console.warn('Date formatting error:', error);
        return 'Invalid Date';
    }
};

const ArchiveGallery = () => {
    const [tab, setTab] = useState('active');
    const [clips, setClips] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedClip, setSelectedClip] = useState(null);
    const [unavailableClips, setUnavailableClips] = useState({});
    const theme = useTheme();

    const handleStreamError = (clipId) => {
        setUnavailableClips(prev => ({ ...prev, [clipId]: true }));
    };

    useEffect(() => {
        fetchClips();
    }, [tab]);

    const fetchClips = async () => {
        console.log('fetchClips called for tab:', tab);
        setLoading(true);
        setUnavailableClips({});
        try {
            let url;
            if (tab === 'bin') {
                url = `${API_BASE_URL}/smart-bin/clips`;
                console.log('Fetching smart bin clips from:', url);
            } else {
                url = `${API_BASE_URL}/archive/list?source=${tab}`;
                console.log('Fetching archive clips from:', url);
            }
            const response = await fetch(url);
            console.log('Response status:', response.status_code);
            
            const data = await response.json();
            console.log('Response data:', data);
            
            if (tab === 'bin') {
                setClips(Array.isArray(data) ? data : []);
                console.log('Set clips (bin):', Array.isArray(data) ? data : []);
            } else {
                setClips(data.clips || []);
                console.log('Set clips (archive):', data.clips || []);
            }
        } catch (error) {
            console.error('Error fetching clips:', error);
            setClips([]);
        } finally {
            setLoading(false);
            console.log('fetchClips completed, loading set to false');
        }
    };

    const handleDownload = (clip) => {
        const link = document.createElement('a');
        link.href = `${API_BASE_URL}${clip.url}`;
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
                                    {tab === 'bin' ? (
                                        /* ── Smart Bin card ── */
                                        <>
                                            <Box sx={{ position: 'relative', height: 160, bgcolor: '#000', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                                {unavailableClips[clip.id] ? (
                                                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1, color: alpha('#fff', 0.5) }}>
                                                        <AlertTriangle size={28} />
                                                        <Typography variant="caption" sx={{ color: alpha('#fff', 0.5), fontWeight: 700 }}>
                                                            Unavailable
                                                        </Typography>
                                                        <IconButton
                                                            size="small"
                                                            onClick={() => {
                                                                console.log(`Retrying clip ${clip.id}`);
                                                                setUnavailableClips(prev => {
                                                                    const newState = { ...prev };
                                                                    delete newState[clip.id];
                                                                    return newState;
                                                                });
                                                            }}
                                                            sx={{
                                                                color: alpha('#fff', 0.7),
                                                                '&:hover': { color: '#fff', bgcolor: alpha('#fff', 0.1) }
                                                            }}
                                                            title="Retry loading video"
                                                        >
                                                            <Refresh size={16} />
                                                        </IconButton>
                                                    </Box>
                                                ) : (
                                                    <Box sx={{ position: 'relative', width: '100%', height: '100%' }}>
                                                        <Typography variant="caption" sx={{ color: '#fff', position: 'absolute', top: 5, left: 5, zIndex: 10 }}>
                                                            Loading video...
                                                        </Typography>
                                                        <video
                                                            key={`video-${clip.id}-${Date.now()}`}
                                                            ref={(videoEl) => {
                                                                if (videoEl && !videoEl.dataset.initialized) {
                                                                    videoEl.dataset.initialized = 'true';
                                                                    console.log(`Initializing video element for clip ${clip.id}`);

                                                                    // Enhanced video element setup for browser compatibility
                                                                    videoEl.crossOrigin = 'anonymous';
                                                                    videoEl.setAttribute('webkit-playsinline', '');
                                                                    videoEl.setAttribute('playsinline', '');
                                                                    videoEl.muted = true;
                                                                    videoEl.preload = 'metadata';

                                                                    // Enhanced error handling with detailed logging
                                                                    videoEl.addEventListener('error', async (e) => {
                                                                        console.error(`Video load error for clip ${clip.id}:`, e);
                                                                        console.error(`Video URL: ${API_BASE_URL}/smart-bin/clips/${clip.id}/stream`);
                                                                        console.error(`Video error code: ${videoEl.error ? videoEl.error.code : 'N/A'}`);
                                                                        console.error(`Video error message: ${videoEl.error ? videoEl.error.message : 'N/A'}`);

                                                                        // Fallback: Try to fetch as blob and create blob URL
                                                                        try {
                                                                            console.log(`Trying blob fallback for clip ${clip.id}`);
                                                                            const response = await fetch(`${API_BASE_URL}/smart-bin/clips/${clip.id}/stream`);
                                                                            if (response.ok) {
                                                                                const blob = await response.blob();
                                                                                const blobUrl = URL.createObjectURL(blob);
                                                                                videoEl.src = blobUrl;
                                                                                console.log(`Blob fallback successful for clip ${clip.id}`);
                                                                            } else {
                                                                                console.error(`Blob fallback failed for clip ${clip.id}: ${response.status}`);
                                                                                handleStreamError(clip.id);
                                                                            }
                                                                        } catch (blobError) {
                                                                            console.error(`Blob fallback error for clip ${clip.id}:`, blobError);
                                                                            handleStreamError(clip.id);
                                                                        }
                                                                    });

                                                                    videoEl.addEventListener('loadstart', () => {
                                                                        console.log(`Starting to load video for clip ${clip.id}`);
                                                                    });

                                                                    videoEl.addEventListener('loadeddata', () => {
                                                                        console.log(`Video loaded successfully for clip ${clip.id}`);
                                                                    });

                                                                    videoEl.addEventListener('stalled', () => {
                                                                        console.warn(`Video loading stalled for clip ${clip.id}`);
                                                                    });

                                                                    videoEl.addEventListener('canplay', () => {
                                                                        console.log(`Video can play for clip ${clip.id}`);
                                                                    });

                                                                    videoEl.addEventListener('canplaythrough', () => {
                                                                        console.log(`Video can play through for clip ${clip.id}`);
                                                                    });

                                                                    videoEl.addEventListener('loadedmetadata', () => {
                                                                        console.log(`Video metadata loaded for clip ${clip.id}`);
                                                                        console.log(`Video duration: ${videoEl.duration}s`);
                                                                        console.log(`Video dimensions: ${videoEl.videoWidth}x${videoEl.videoHeight}`);

                                                                        // Try to play automatically after metadata loads
                                                                        const playPromise = videoEl.play();
                                                                        if (playPromise !== undefined) {
                                                                            playPromise.then(() => {
                                                                                console.log(`Video autoplay started for clip ${clip.id}`);
                                                                            }).catch(error => {
                                                                                console.log(`Video autoplay failed for clip ${clip.id}: ${error.message}`);
                                                                                // Add user interaction hint
                                                                                videoEl.setAttribute('controls', '');
                                                                            });
                                                                        }
                                                                    });

                                                                    // Force load after a short delay
                                                                    setTimeout(() => {
                                                                        if (videoEl.readyState === 0) {
                                                                            console.log(`Forcing video load for clip ${clip.id}`);
                                                                            videoEl.load();
                                                                        }
                                                                    }, 100);
                                                                }
                                                            }}
                                                            src={`${API_BASE_URL}/smart-bin/clips/${clip.id}/stream`}
                                                            controls
                                                            style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                                                            preload="metadata"
                                                            playsInline
                                                            muted
                                                        />
                                                    </Box>
                                                )}
                                            </Box>
                                            <CardContent sx={{ p: 2 }}>
                                                <Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                    Camera: {clip.camera_id}
                                                </Typography>
                                                {/* Location label */}
                                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1, opacity: 0.7 }}>
                                                    <MapPin size={12} />
                                                    <Typography variant="caption" sx={{ fontWeight: 600 }}>
                                                        {clip.location ? clip.location : 'Unknown Location'}
                                                    </Typography>
                                                </Box>
                                                <Typography variant="caption" sx={{ opacity: 0.6, fontWeight: 600 }}>
                                                    Captured: {format(new Date(clip.captured_at), 'MMM d, yyyy')}
                                                </Typography>
                                                <Typography variant="caption" sx={{ opacity: 0.6, fontWeight: 600 }}>
                                                    Expires: {format(new Date(clip.expires_at), 'MMM d, yyyy')}
                                                </Typography>
                                            </CardContent>
                                        </>
                                    ) : (
                                        /* ── Active Alerts card (unchanged) ── */
                                        <>
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
                                                <Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 0.5, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
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
                                        </>
                                    )}
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
                            src={`${API_BASE_URL}${selectedClip.url}`}
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
