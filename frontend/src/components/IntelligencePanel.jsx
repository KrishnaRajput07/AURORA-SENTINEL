import React, { useState, useEffect } from 'react';
import {
    Box, Typography, Paper, TextField, IconButton, Chip,
    List, ListItem, ListItemText, ListItemIcon,
    Divider, alpha, useTheme, CircularProgress,
    Button, Badge, Avatar, Fade, Tooltip,
    Modal, Backdrop
} from '@mui/material';
import {
    Search, Brain, Play, Clock, AlertTriangle,
    Activity, Filter, History, Target, ShieldAlert,
    Zap, Mic, Video, X
} from 'lucide-react';
import { API_BASE_URL } from '../config';
import { useIntelligence } from '../context/IntelligenceContext';

const IntelligencePanel = ({ currentFile }) => {
    const { setDrawerOpen, setSeekSeconds } = useIntelligence();
    const [selectedSeverity, setSelectedSeverity] = useState('ALL');
    const [selectedThreat, setSelectedThreat] = useState(null);
    const [activeTab, setActiveTab] = useState('latest');
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [latestEvents, setLatestEvents] = useState([]);
    const [isSearching, setIsSearching] = useState(false);
    const [selectedVideo, setSelectedVideo] = useState(null);
    const [chatAnswer, setChatAnswer] = useState(null);
    const [isChatting, setIsChatting] = useState(false);
    const [chatQuery, setChatQuery] = useState('');
    const [chatHistory, setChatHistory] = useState([]);

    const theme = useTheme();

    // NEW: Auto-filter/reset when current file changes
    useEffect(() => {
        if (currentFile) {
            setQuery("");
            setResults([]);
            // Don't auto-switch tabs - let user choose
            // Auto-trigger search only if already on search tab
            if (activeTab === 'search') {
                handleSearch();
            }
        } else {
            setResults([]);
            setLatestEvents([]);
        }
    }, [currentFile]);

    useEffect(() => {
        fetchLatest();
    }, []);

    const fetchLatest = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/intelligence/latest`);
            const data = await res.json();
            setLatestEvents(data);
        } catch (e) {
            console.error("Failed to fetch latest:", e);
        }
    };

    const handleChat = async (e, customQuestion = null) => {
        if (e) e.preventDefault();
        const questionToAsk = customQuestion || chatQuery;
        
        if (!questionToAsk) {
            setChatHistory(prev => [...prev, { type: 'error', message: "Please type a question." }]);
            return;
        }

        setChatHistory(prev => [...prev, { type: 'user', message: questionToAsk }]);
        setIsChatting(true);
        setChatQuery('');
        
        try {
            const history = chatHistory.slice(-6).map(m => ({
                role: m.type === 'user' ? 'user' : 'assistant',
                content: m.message
            }));

            // Always use the NLU chatbot.
            // Pass filename if a video is loaded — backend will use stored metadata for video Q&A.
            const res = await fetch(`${API_BASE_URL}/chatbot/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: questionToAsk,
                    history,
                    filename: currentFile || null,
                })
            });
            if (!res.ok) throw new Error(`Server returned ${res.status}`);
            const data = await res.json();
            setChatHistory(prev => [...prev, {
                type: 'ai',
                message: data.answer || "No results found.",
                results: data.results || [],
                result_type: data.result_type || 'none',
                confidence: data.confidence ?? null,
                vlm_verified: data.vlm_verified || false,
                filename: currentFile || null,
            }]);
        } catch (err) {
            console.error("Chat failed:", err);
            setChatHistory(prev => [...prev, {
                type: 'error',
                message: `Error: ${err.message}`
            }]);
        } finally {
            setIsChatting(false);
        }
    };

    const handleSearch = async (e) => {
        if (e) e.preventDefault();

        setIsSearching(true);
        setActiveTab('search');
        try {
            const baseUrl = `${API_BASE_URL}/intelligence/search`;
            const params = new URLSearchParams({ q: query || "general description" });
            if (currentFile) params.append('filename', currentFile);

            const res = await fetch(`${baseUrl}?${params.toString()}`);
            const data = await res.json();
            setResults(data);
        } catch (e) {
            console.error("Search failed:", e);
        } finally {
            setIsSearching(false);
        }
    };

    const getFilteredResults = () => {
        const source = (activeTab === 'latest' ? latestEvents : results) || [];
        return source.filter(item => {
            if (selectedSeverity !== 'ALL') {
                const itemSev = (item.severity || 'low').toUpperCase();
                if (itemSev !== selectedSeverity) return false;
            }
            if (selectedThreat) {
                const threats = (item.threats || []).map(t => t.toLowerCase());
                const desc = (item.description || '').toLowerCase();
                const term = selectedThreat.toLowerCase();
                if (!threats.includes(term) && !desc.includes(term)) return false;
            }
            return true;
        });
    };

    const filteredResults = getFilteredResults();

    const SeverityChip = ({ severity }) => {
        const sev = (severity || 'low').toUpperCase();
        let color = theme.palette.success;
        if (sev === 'HIGH') color = theme.palette.error;
        if (sev === 'MEDIUM') color = theme.palette.warning;
        if (sev === 'SPORT_BOXING' || sev === 'LOW') color = theme.palette.info;

        return (
            <Chip
                label={sev}
                size="small"
                sx={{
                    bgcolor: alpha(color.main, 0.1),
                    color: color.main,
                    fontWeight: 900,
                    fontSize: '0.65rem',
                    height: 20,
                    borderRadius: 1
                }}
            />
        );
    };

    return (
        <Box sx={{
            bgcolor: '#0f172a', // Deep slate background
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            width: 400,
            borderLeft: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
            boxShadow: '-10px 0 30px rgba(0,0,0,0.2)'
        }}>
            {/* Header Section */}
            <Box sx={{ p: 3, borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}` }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                    <Avatar sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1), width: 32, height: 32 }}>
                        <Brain size={18} color={theme.palette.primary.main} />
                    </Avatar>
                    <Typography variant="h6" sx={{ fontWeight: 900, color: '#f8fafc', letterSpacing: '0.05em' }}>
                        CORTEX <Typography component="span" sx={{ color: theme.palette.primary.main, fontWeight: 900 }}>VLM</Typography>
                    </Typography>
                </Box>

                {/* Search Bar */}
                <Box component="form" onSubmit={handleSearch} sx={{ position: 'relative', mb: 2 }}>
                    <TextField
                        fullWidth
                        size="small"
                        placeholder="Neural search, e.g. 'fights'..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        variant="outlined"
                        sx={{
                            '& .MuiOutlinedInput-root': {
                                bgcolor: 'rgba(0,0,0,0.3)',
                                borderRadius: 3,
                                color: '#fff',
                                fontWeight: 600,
                                fontSize: '0.85rem',
                                '& fieldset': { borderColor: alpha(theme.palette.divider, 0.1) },
                                '&:hover fieldset': { borderColor: alpha(theme.palette.primary.main, 0.3) },
                                '&.Mui-focused fieldset': { borderColor: theme.palette.primary.main },
                            }
                        }}
                    />
                    <IconButton
                        type="submit"
                        sx={{ position: 'absolute', right: 4, top: 4, color: theme.palette.primary.main }}
                    >
                        <Search size={18} />
                    </IconButton>
                </Box>

                {/* Quick Filters */}
                <Box sx={{ display: 'flex', gap: 1, overflowX: 'auto', pb: 1, '&::-webkit-scrollbar': { display: 'none' } }}>
                    {['GUN', 'KNIFE', 'FIGHT', 'FIRE', 'BLOOD'].map(threat => (
                        <Chip
                            key={threat}
                            label={threat}
                            onClick={() => setSelectedThreat(selectedThreat === threat ? null : threat)}
                            size="small"
                            sx={{
                                fontWeight: 800,
                                fontSize: '0.65rem',
                                bgcolor: selectedThreat === threat ? alpha(theme.palette.error.main, 0.2) : 'rgba(255,255,255,0.05)',
                                color: selectedThreat === threat ? theme.palette.error.main : 'rgba(255,255,255,0.4)',
                                border: `1px solid ${selectedThreat === threat ? theme.palette.error.main : 'transparent'}`,
                                '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.1) }
                            }}
                        />
                    ))}
                </Box>
            </Box>

            {/* Navigation Tabs */}
            <Box sx={{ display: 'flex', px: 2, py: 1, gap: 1, bgcolor: alpha('#000', 0.2) }}>
                <Button
                    size="small"
                    startIcon={<History size={14} />}
                    onClick={() => setActiveTab('latest')}
                    sx={{
                        borderRadius: 2,
                        fontWeight: 800,
                        color: activeTab === 'latest' ? theme.palette.primary.main : 'rgba(255,255,255,0.4)',
                        bgcolor: activeTab === 'latest' ? alpha(theme.palette.primary.main, 0.1) : 'transparent'
                    }}
                >
                    LATEST
                </Button>
                <Button
                    size="small"
                    startIcon={<Target size={14} />}
                    onClick={() => setActiveTab('search')}
                    sx={{
                        borderRadius: 2,
                        fontWeight: 800,
                        color: activeTab === 'search' ? theme.palette.primary.main : 'rgba(255,255,255,0.4)',
                        bgcolor: activeTab === 'search' ? alpha(theme.palette.primary.main, 0.1) : 'transparent'
                    }}
                >
                    RESULTS
                </Button>
                <Button
                    size="small"
                    startIcon={<Brain size={14} />}
                    onClick={() => setActiveTab('chat')}
                    sx={{
                        borderRadius: 2,
                        fontWeight: 800,
                        color: activeTab === 'chat' ? theme.palette.secondary.main : 'rgba(255,255,255,0.4)',
                        bgcolor: activeTab === 'chat' ? alpha(theme.palette.secondary.main, 0.1) : 'transparent'
                    }}
                >
                    CHAT
                </Button>
                <Tooltip title="Neural Refresher">
                    <IconButton size="small" onClick={fetchLatest} sx={{ ml: 'auto', color: 'rgba(255,255,255,0.3)' }}>
                        <Zap size={14} />
                    </IconButton>
                </Tooltip>
            </Box>

            {/* Content Area */}
            <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
                {isSearching ? (
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 10, gap: 2 }}>
                        <CircularProgress size={40} thickness={6} sx={{ color: theme.palette.primary.main }} />
                        <Typography variant="caption" sx={{ fontWeight: 800, color: 'rgba(255,255,255,0.3)', letterSpacing: '0.1em' }}>
                            QUERYING COGNITIVE INDEX...
                        </Typography>
                    </Box>
                ) : filteredResults.length > 0 ? (
                    <List disablePadding>
                        {filteredResults.map((item, idx) => {
                            // Filter out technical noise from UI (Innovation #25)
                            if (item.description && (item.description.includes("Error:") || item.description.toLowerCase().includes("rate limit"))) {
                                return null;
                            }

                            const isAudio = item.provider === 'audio-ast';
                            const score = item.score ? Math.round(item.score * 100) : null;
                            const isCritical = (item.severity || '').toLowerCase() === 'high' || (score && score > 70);

                            return (
                                <Fade in key={idx} timeout={300 + (idx * 100)}>
                                    <Paper
                                        onClick={() => setSelectedVideo(item)}
                                        sx={{
                                            mb: 2,
                                            p: 2,
                                            borderRadius: 3,
                                            cursor: 'pointer',
                                            bgcolor: isCritical ? alpha(theme.palette.error.main, 0.03) : 'rgba(255,255,255,0.02)',
                                            border: `1px solid ${isCritical ? alpha(theme.palette.error.main, 0.2) : alpha(theme.palette.divider, 0.05)}`,
                                            '&:hover': {
                                                bgcolor: 'rgba(255,255,255,0.04)',
                                                borderColor: alpha(theme.palette.primary.main, 0.3),
                                                transform: 'translateY(-2px)'
                                            },
                                            transition: 'all 0.2s'
                                        }}
                                    >
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                {isAudio ? <Mic size={14} color="#818cf8" /> : <Video size={14} color="#22d3ee" />}
                                                <Typography variant="caption" sx={{ fontWeight: 900, color: 'rgba(255,255,255,0.4)', fontSize: '0.7rem' }}>
                                                    {isAudio ? 'SONIC DETECTOR' : (item.filename && !item.filename.toLowerCase().startsWith('test')) ? item.filename.split('_')[0].toUpperCase() : 'SECURED STREAM'}
                                                </Typography>
                                            </Box>
                                            <SeverityChip severity={item.severity} />
                                        </Box>

                                        <Typography variant="body2" sx={{
                                            color: '#cbd5e1',
                                            fontSize: '0.85rem',
                                            lineHeight: 1.5,
                                            mb: 2,
                                            fontWeight: 500,
                                            display: '-webkit-box',
                                            WebkitLineClamp: 3,
                                            WebkitBoxOrient: 'vertical',
                                            overflow: 'hidden'
                                        }}>
                                            {item.description}
                                        </Typography>

                                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Clock size={12} color="gray" />
                                                <Typography variant="caption" sx={{ fontFamily: 'monospace', color: 'rgba(255,255,255,0.3)', fontWeight: 700 }}>
                                                    {item.timestamp}s
                                                </Typography>
                                            </Box>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Typography variant="caption" sx={{ fontWeight: 900, fontSize: '0.6rem', color: theme.palette.primary.main }}>
                                                    VIEW BRIEF
                                                </Typography>
                                            </Box>
                                        </Box>
                                    </Paper>
                                </Fade>
                            );
                        })
                        }
                    </List>
                ) : activeTab === 'chat' ? (
                    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                        {/* Chat History */}
                        <Box sx={{ flexGrow: 1, overflowY: 'auto', mb: 2 }}>
                            {chatHistory.length === 0 ? (
                                <Box sx={{ textAlign: 'center', mt: 5 }}>
                                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.2)', fontWeight: 800, mb: 3 }}>
                                        {currentFile ? 'ASK A QUESTION ABOUT THE VIDEO' : 'ASK ABOUT ALERTS & INCIDENTS'}
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, px: 2 }}>
                                        {currentFile ? (
                                            <>
                                                <Button variant="outlined" color="secondary"
                                                    onClick={(e) => handleChat(e, "What is happening in this video?")}
                                                    sx={{ borderRadius: 2, fontWeight: 800 }}>
                                                    Summarize Video
                                                </Button>
                                                <Button variant="outlined" color="secondary"
                                                    onClick={(e) => handleChat(e, "Is this a real fight or boxing/sparring?")}
                                                    sx={{ borderRadius: 2, fontWeight: 800 }}>
                                                    Fight vs Boxing?
                                                </Button>
                                                <Button variant="outlined" color="secondary"
                                                    onClick={(e) => handleChat(e, "Are there any weapons visible?")}
                                                    sx={{ borderRadius: 2, fontWeight: 800 }}>
                                                    Weapons Detected?
                                                </Button>
                                                <Button variant="outlined" color="warning"
                                                    onClick={(e) => handleChat(e, "Show high risk alerts today")}
                                                    sx={{ borderRadius: 2, fontWeight: 800 }}>
                                                    Today's Alerts
                                                </Button>
                                                <Button variant="outlined" color="warning"
                                                    onClick={(e) => handleChat(e, "System overview")}
                                                    sx={{ borderRadius: 2, fontWeight: 800 }}>
                                                    System Overview
                                                </Button>
                                            </>
                                        ) : (
                                            <>
                                                <Button variant="outlined" color="secondary"
                                                    onClick={(e) => handleChat(e, "Show high risk alerts today")}
                                                    sx={{ borderRadius: 2, fontWeight: 800 }}>
                                                    Today's High Risk Alerts
                                                </Button>
                                                <Button variant="outlined" color="secondary"
                                                    onClick={(e) => handleChat(e, "Find fights in the last hour")}
                                                    sx={{ borderRadius: 2, fontWeight: 800 }}>
                                                    Recent Fights
                                                </Button>
                                                <Button variant="outlined" color="secondary"
                                                    onClick={(e) => handleChat(e, "System overview")}
                                                    sx={{ borderRadius: 2, fontWeight: 800 }}>
                                                    System Overview
                                                </Button>
                                                <Button variant="outlined" color="secondary"
                                                    onClick={(e) => handleChat(e, "Show critical incidents last night")}
                                                    sx={{ borderRadius: 2, fontWeight: 800 }}>
                                                    Last Night's Incidents
                                                </Button>
                                            </>
                                        )}
                                    </Box>
                                </Box>
                            ) : (
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                    {chatHistory.map((msg, idx) => (
                                        <Box key={idx} sx={{
                                            display: 'flex',
                                            justifyContent: msg.type === 'user' ? 'flex-end' : 'flex-start'
                                        }}>
                                            <Paper sx={{
                                                p: 2,
                                                borderRadius: 3,
                                                maxWidth: '85%',
                                                bgcolor: msg.type === 'user' 
                                                    ? alpha(theme.palette.primary.main, 0.1)
                                                    : msg.type === 'error'
                                                    ? alpha(theme.palette.error.main, 0.1)
                                                    : alpha(theme.palette.secondary.main, 0.05),
                                                border: `1px solid ${
                                                    msg.type === 'user'
                                                    ? alpha(theme.palette.primary.main, 0.3)
                                                    : msg.type === 'error'
                                                    ? alpha(theme.palette.error.main, 0.3)
                                                    : alpha(theme.palette.secondary.main, 0.2)
                                                }`
                                            }}>
                                                {msg.type === 'ai' && msg.filename && (
                                                    <Typography variant="caption" sx={{ 
                                                        color: 'rgba(255,255,255,0.4)', 
                                                        fontWeight: 800,
                                                        display: 'block',
                                                        mb: 1
                                                    }}>
                                                        📹 {msg.filename}
                                                    </Typography>
                                                )}
                                                <Typography variant="body2" sx={{ 
                                                    color: '#fff', 
                                                    lineHeight: 1.6, 
                                                    fontWeight: 500,
                                                    whiteSpace: 'pre-wrap'
                                                }}>
                                                    {msg.message}
                                                </Typography>
                                                {msg.type === 'ai' && msg.confidence !== undefined && msg.confidence !== null && (
                                                    <Typography variant="caption" sx={{ 
                                                        color: 'rgba(255,255,255,0.3)', 
                                                        fontWeight: 700,
                                                        display: 'block',
                                                        mt: 1
                                                    }}>
                                                        Confidence: {(msg.confidence * 100).toFixed(0)}%
                                                        {msg.vlm_verified && ' · ✓ VLM Verified'}
                                                    </Typography>
                                                )}
                                                {/* Alert result cards */}
                                                {msg.type === 'ai' && msg.results?.length > 0 && (
                                                    <Box sx={{ mt: 1.5 }}>
                                                        {msg.result_type === 'stats' && msg.results.map((r, i) => (
                                                            <Box key={i} sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mt: 1 }}>
                                                                {[['Total', r.total_alerts], ['Today', r.today], ['Critical', r.critical], ['Pending', r.pending]].map(([label, val]) => (
                                                                    <Box key={label} sx={{ bgcolor: 'rgba(255,255,255,0.05)', borderRadius: 1, p: 1, textAlign: 'center' }}>
                                                                        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.4)', display: 'block' }}>{label}</Typography>
                                                                        <Typography variant="body2" sx={{ fontWeight: 800, color: '#fff' }}>{val}</Typography>
                                                                    </Box>
                                                                ))}
                                                            </Box>
                                                        ))}
                                                        {msg.result_type === 'alerts' && msg.results.slice(0, 5).map((r, i) => {
                                                            const levelColor = { CRITICAL: '#ef4444', HIGH: '#f97316', MEDIUM: '#eab308', LOW: '#22c55e' }[r.level?.toUpperCase()] || '#6b7280';
                                                            const ts = r.timestamp ? r.timestamp.replace('T', ' ').slice(0, 16) : '';
                                                            return (
                                                                <Box key={i} sx={{ mt: 1, p: 1.5, borderRadius: 1, bgcolor: 'rgba(255,255,255,0.03)', borderLeft: `3px solid ${levelColor}` }}>
                                                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                                                                        <Typography variant="caption" sx={{ fontWeight: 800, color: levelColor }}>{r.level?.toUpperCase()}</Typography>
                                                                        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.4)' }}>{ts}</Typography>
                                                                    </Box>
                                                                    <Typography variant="caption" sx={{ color: '#cbd5e1', display: 'block' }}>{r.camera_id} — {r.location}</Typography>
                                                                    {r.ai_explanation && <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.4)', fontStyle: 'italic', display: 'block', mt: 0.5 }}>{r.ai_explanation.slice(0, 80)}...</Typography>}
                                                                    {r.clip_url && (
                                                                        <Typography component="a" href={`${API_BASE_URL}${r.clip_url}`} target="_blank"
                                                                            variant="caption" sx={{ color: theme.palette.primary.main, fontWeight: 700, display: 'block', mt: 0.5 }}>
                                                                            ▶ Play Clip
                                                                        </Typography>
                                                                    )}
                                                                </Box>
                                                            );
                                                        })}
                                                        {msg.result_type === 'video_events' && msg.results.slice(0, 5).map((r, i) => (
                                                            <Box key={i} sx={{ mt: 1, p: 1.5, borderRadius: 1, bgcolor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                                                                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                                                                    <Typography variant="caption" sx={{ fontWeight: 800, color: theme.palette.primary.main }}>{r.filename}</Typography>
                                                                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.4)' }}>@{r.timestamp?.toFixed(1)}s</Typography>
                                                                </Box>
                                                                <Typography variant="caption" sx={{ color: '#cbd5e1', display: 'block' }}>{r.description?.slice(0, 100)}...</Typography>
                                                            </Box>
                                                        ))}
                                                    </Box>
                                                )}
                                            </Paper>
                                        </Box>
                                    ))}
                                    {isChatting && (
                                        <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
                                            <Paper sx={{
                                                p: 2,
                                                borderRadius: 3,
                                                bgcolor: alpha(theme.palette.secondary.main, 0.05),
                                                border: `1px solid ${alpha(theme.palette.secondary.main, 0.2)}`,
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: 1
                                            }}>
                                                <CircularProgress size={16} color="secondary" />
                                                <Typography variant="caption" sx={{ fontWeight: 800, color: 'rgba(255,255,255,0.3)' }}>
                                                    THINKING...
                                                </Typography>
                                            </Paper>
                                        </Box>
                                    )}
                                </Box>
                            )}
                        </Box>

                        {/* Chat Input */}
                        <Box component="form" onSubmit={handleChat} sx={{ 
                            position: 'sticky', 
                            bottom: 0, 
                            bgcolor: '#0f172a',
                            pt: 2,
                            borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}`
                        }}>
                            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                                <TextField
                                    fullWidth
                                    size="small"
                                    placeholder={currentFile ? "Ask about video or alerts/incidents..." : "Ask about alerts, incidents, counts..."}
                                    value={chatQuery}
                                    onChange={(e) => setChatQuery(e.target.value)}
                                    disabled={isChatting}
                                    variant="outlined"
                                    sx={{
                                        '& .MuiOutlinedInput-root': {
                                            bgcolor: 'rgba(0,0,0,0.3)',
                                            borderRadius: 3,
                                            color: '#fff',
                                            fontWeight: 600,
                                            fontSize: '0.85rem',
                                            '& fieldset': { borderColor: alpha(theme.palette.divider, 0.1) },
                                            '&:hover fieldset': { borderColor: alpha(theme.palette.secondary.main, 0.3) },
                                            '&.Mui-focused fieldset': { borderColor: theme.palette.secondary.main },
                                        }
                                    }}
                                />
                                <IconButton
                                    type="submit"
                                    disabled={isChatting || (!chatQuery && !currentFile)}
                                    sx={{ 
                                        color: theme.palette.secondary.main,
                                        bgcolor: alpha(theme.palette.secondary.main, 0.1),
                                        '&:hover': {
                                            bgcolor: alpha(theme.palette.secondary.main, 0.2)
                                        },
                                        '&.Mui-disabled': {
                                            color: 'rgba(255,255,255,0.2)'
                                        }
                                    }}
                                >
                                    <Brain size={18} />
                                </IconButton>
                            </Box>
                            {chatHistory.length > 0 && (
                                <Button
                                    size="small"
                                    onClick={() => setChatHistory([])}
                                    sx={{ mt: 1, fontWeight: 800, fontSize: '0.65rem', color: 'rgba(255,255,255,0.3)' }}
                                >
                                    CLEAR CHAT
                                </Button>
                            )}
                        </Box>
                    </Box>
                ) : (
                    <Box sx={{ textAlign: 'center', mt: 10 }}>
                        <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.2)', fontWeight: 800 }}>
                            NO DATA MATCHES FILTERS
                        </Typography>
                    </Box>
                )}
            </Box>

            {/* FORENSIC BRIEF MODAL */}
            <Modal
                open={!!selectedVideo}
                onClose={() => setSelectedVideo(null)}
                closeAfterTransition
                BackdropComponent={Backdrop}
                BackdropProps={{
                    timeout: 500,
                    sx: { backdropFilter: 'blur(10px)', bgcolor: 'rgba(0,0,0,0.8)' }
                }}
            >
                <Fade in={!!selectedVideo}>
                    <Box sx={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        width: { xs: '90%', md: 700 },
                        maxHeight: '85vh',
                        bgcolor: '#0f172a',
                        border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
                        borderRadius: 6,
                        boxShadow: '0 40px 100px rgba(0,0,0,0.6)',
                        p: 0,
                        overflow: 'hidden',
                        display: 'flex',
                        flexDirection: 'column'
                    }}>
                        {/* Modal Header */}
                        <Box sx={{ p: 3, borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center', bgcolor: alpha('#fff', 0.02) }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                <Avatar sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1), width: 40, height: 40 }}>
                                    <ShieldAlert size={24} color={theme.palette.primary.main} />
                                </Avatar>
                                <Box>
                                    <Typography variant="h6" sx={{ fontWeight: 900, color: '#fff', fontSize: '1rem', mb: -0.5 }}>FORENSIC INTELLIGENCE BRIEF</Typography>
                                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.4)', fontWeight: 800 }}>VLM DERIVED ARCHAEOLOGY</Typography>
                                </Box>
                            </Box>
                            <IconButton onClick={() => setSelectedVideo(null)} sx={{ color: 'rgba(255,255,255,0.3)' }}>
                                <X size={20} />
                            </IconButton>
                        </Box>

                        {/* Modal Content */}
                        <Box sx={{ p: 4, overflowY: 'auto', flexGrow: 1 }}>
                            <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
                                <Paper sx={{ flex: 1, p: 2, borderRadius: 3, bgcolor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                                    <Typography variant="caption" sx={{ fontWeight: 900, color: theme.palette.primary.main, mb: 1, display: 'block' }}>FILE REFERENCE</Typography>
                                    <Typography sx={{ color: '#fff', fontWeight: 700, fontSize: '0.9rem' }}>{selectedVideo?.filename || 'System-Rec-01.mp4'}</Typography>
                                </Paper>
                                <Paper sx={{ flex: 1, p: 2, borderRadius: 3, bgcolor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                                    <Typography variant="caption" sx={{ fontWeight: 900, color: theme.palette.primary.main, mb: 1, display: 'block' }}>TIMESTAMP</Typography>
                                    <Typography sx={{ color: '#fff', fontWeight: 700, fontSize: '0.9rem' }}>{selectedVideo?.timestamp}s</Typography>
                                </Paper>
                            </Box>

                            <Typography variant="caption" sx={{ fontWeight: 900, color: 'rgba(255,255,255,0.3)', mb: 2, display: 'block', letterSpacing: '0.1em' }}>NEURAL DESCRIPTION</Typography>
                            <Typography sx={{
                                color: '#cbd5e1',
                                fontSize: '1.05rem',
                                lineHeight: 1.8,
                                fontWeight: 500,
                                whiteSpace: 'pre-wrap',
                                fontFamily: 'Inter, sans-serif'
                            }}>
                                {selectedVideo?.description}
                            </Typography>
                        </Box>

                        {/* Modal Footer */}
                        <Box sx={{ p: 3, borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}`, bgcolor: alpha('#000', 0.2), display: 'flex', gap: 2 }}>
                            <Button
                                fullWidth
                                variant="contained"
                                startIcon={<Play size={18} />}
                                sx={{ borderRadius: 3, fontWeight: 900, py: 1.5 }}
                                onClick={() => {
                                    // Only reliable when searching within the currently uploaded file
                                    const ts = Number(selectedVideo?.timestamp) || 0;
                                    setDrawerOpen(true);
                                    setSeekSeconds(ts);
                                    setSelectedVideo(null);
                                }}
                            >
                                SEEK TO FRAME
                            </Button>
                        </Box>
                    </Box>
                </Fade>
            </Modal>
        </Box >
    );
};

export default IntelligencePanel;
