import React, { useState, useRef, useEffect } from 'react';
import {
    Box, Paper, Typography, TextField, IconButton, Chip,
    CircularProgress, Fade, Avatar, alpha, useTheme,
    List, ListItem, ListItemText, Divider, Badge, Tooltip,
    Collapse,
} from '@mui/material';
import {
    MessageSquare, Send, X, Bot, User, AlertTriangle,
    Video, BarChart2, ChevronDown, ChevronUp, Play,
    Zap, Clock, Shield,
} from 'lucide-react';
import { API_BASE_URL } from '../config';
import { format } from 'date-fns';

// ---------------------------------------------------------------------------
// Result card renderers
// ---------------------------------------------------------------------------

const AlertCard = ({ item }) => {
    const theme = useTheme();
    const levelColor = {
        CRITICAL: '#ef4444', HIGH: '#f97316', MEDIUM: '#eab308', LOW: '#22c55e',
    }[item.level?.toUpperCase()] || '#6b7280';

    const ts = item.timestamp ? item.timestamp.replace('T', ' ').slice(0, 16) : '';

    return (
        <Paper variant="outlined" sx={{ p: 1.5, mb: 1, borderLeft: `3px solid ${levelColor}`, borderRadius: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                <Chip label={item.level?.toUpperCase()} size="small"
                    sx={{ bgcolor: alpha(levelColor, 0.15), color: levelColor, fontWeight: 700, fontSize: '0.65rem' }} />
                <Typography variant="caption" color="text.secondary">{ts}</Typography>
            </Box>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>{item.camera_id}</Typography>
            <Typography variant="caption" color="text.secondary">{item.location}</Typography>
            {item.ai_explanation && (
                <Typography variant="caption" sx={{ display: 'block', mt: 0.5, opacity: 0.7, fontStyle: 'italic' }}>
                    {item.ai_explanation.slice(0, 100)}...
                </Typography>
            )}
            {item.clip_url && (
                <Box sx={{ mt: 0.5 }}>
                    <Chip
                        icon={<Play size={10} />}
                        label="Play Clip"
                        size="small"
                        clickable
                        component="a"
                        href={`${API_BASE_URL}${item.clip_url}`}
                        target="_blank"
                        sx={{ fontSize: '0.65rem' }}
                    />
                </Box>
            )}
        </Paper>
    );
};

const VideoEventCard = ({ item }) => (
    <Paper variant="outlined" sx={{ p: 1.5, mb: 1, borderRadius: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="caption" sx={{ fontWeight: 700, color: 'primary.main' }}>
                {item.filename}
            </Typography>
            <Typography variant="caption" color="text.secondary">@{item.timestamp?.toFixed(1)}s</Typography>
        </Box>
        <Typography variant="caption" sx={{ display: 'block' }}>{item.description?.slice(0, 120)}...</Typography>
        {item.threats?.filter(Boolean).length > 0 && (
            <Box sx={{ mt: 0.5, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                {item.threats.filter(Boolean).map(t => (
                    <Chip key={t} label={t} size="small" color="warning" variant="outlined"
                        sx={{ fontSize: '0.6rem', height: 18 }} />
                ))}
            </Box>
        )}
    </Paper>
);

const StatsCard = ({ item }) => (
    <Paper variant="outlined" sx={{ p: 1.5, borderRadius: 1 }}>
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
            {[
                { label: 'Total Alerts', value: item.total_alerts, icon: <AlertTriangle size={14} /> },
                { label: 'Today', value: item.today, icon: <Clock size={14} /> },
                { label: 'Critical', value: item.critical, icon: <Shield size={14} /> },
                { label: 'Pending', value: item.pending, icon: <Zap size={14} /> },
            ].map(({ label, value, icon }) => (
                <Box key={label} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Box sx={{ color: 'primary.main' }}>{icon}</Box>
                    <Box>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', lineHeight: 1 }}>{label}</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 700 }}>{value}</Typography>
                    </Box>
                </Box>
            ))}
        </Box>
    </Paper>
);

// ---------------------------------------------------------------------------
// Message bubble
// ---------------------------------------------------------------------------

const MessageBubble = ({ msg }) => {
    const theme = useTheme();
    const isUser = msg.role === 'user';
    const [expanded, setExpanded] = useState(true);

    const renderMarkdown = (text) => {
        // Simple bold + newline rendering
        return text.split('\n').map((line, i) => {
            const parts = line.split(/\*\*(.*?)\*\*/g);
            return (
                <span key={i}>
                    {parts.map((p, j) => j % 2 === 1 ? <strong key={j}>{p}</strong> : p)}
                    {i < text.split('\n').length - 1 && <br />}
                </span>
            );
        });
    };

    return (
        <Box sx={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', mb: 1.5, gap: 1 }}>
            {!isUser && (
                <Avatar sx={{ width: 28, height: 28, bgcolor: 'primary.main', flexShrink: 0, mt: 0.5 }}>
                    <Bot size={14} />
                </Avatar>
            )}
            <Box sx={{ maxWidth: '85%' }}>
                <Paper sx={{
                    p: 1.5,
                    bgcolor: isUser ? 'primary.main' : alpha(theme.palette.background.paper, 0.9),
                    color: isUser ? '#fff' : 'text.primary',
                    borderRadius: isUser ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                    boxShadow: 'none',
                    border: isUser ? 'none' : `1px solid ${theme.palette.divider}`,
                }}>
                    <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                        {renderMarkdown(msg.content)}
                    </Typography>
                </Paper>

                {/* Results */}
                {msg.results?.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                        <Box
                            sx={{ display: 'flex', alignItems: 'center', gap: 0.5, cursor: 'pointer', mb: 0.5 }}
                            onClick={() => setExpanded(e => !e)}
                        >
                            <Typography variant="caption" color="primary" sx={{ fontWeight: 600 }}>
                                {msg.results.length} result{msg.results.length > 1 ? 's' : ''}
                            </Typography>
                            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                        </Box>
                        <Collapse in={expanded}>
                            <Box sx={{ maxHeight: 320, overflowY: 'auto' }}>
                                {msg.result_type === 'alerts' && msg.results.map((r, i) => <AlertCard key={i} item={r} />)}
                                {msg.result_type === 'video_events' && msg.results.map((r, i) => <VideoEventCard key={i} item={r} />)}
                                {msg.result_type === 'stats' && msg.results.map((r, i) => <StatsCard key={i} item={r} />)}
                            </Box>
                        </Collapse>
                    </Box>
                )}

                <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 0.5, textAlign: isUser ? 'right' : 'left' }}>
                    {format(new Date(msg.timestamp), 'HH:mm')}
                </Typography>
            </Box>
            {isUser && (
                <Avatar sx={{ width: 28, height: 28, bgcolor: 'grey.300', flexShrink: 0, mt: 0.5 }}>
                    <User size={14} />
                </Avatar>
            )}
        </Box>
    );
};

// ---------------------------------------------------------------------------
// Main chatbot component
// ---------------------------------------------------------------------------

export default function SurveillanceChatbot() {
    const theme = useTheme();
    const [open, setOpen] = useState(false);
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: "Hi! I'm your surveillance assistant. Ask me about alerts, incidents, or video events.\n\nTry: **'Show high risk alerts today'** or **'Find fights in the last hour'**",
            results: [],
            result_type: 'none',
            timestamp: new Date().toISOString(),
        }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [suggestions, setSuggestions] = useState([]);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    useEffect(() => {
        if (open) {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    }, [open, messages]);

    const fetchSuggestions = async (q) => {
        if (!q || q.length < 2) { setSuggestions([]); return; }
        try {
            const res = await fetch(`${API_BASE_URL}/chatbot/suggestions?q=${encodeURIComponent(q)}`);
            const data = await res.json();
            setSuggestions(data.suggestions || []);
        } catch { setSuggestions([]); }
    };

    const sendMessage = async (text) => {
        const msg = (text || input).trim();
        if (!msg) return;

        const userMsg = { role: 'user', content: msg, results: [], result_type: 'none', timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setSuggestions([]);
        setLoading(true);

        try {
            const history = messages.slice(-6).map(m => ({ role: m.role, content: m.content }));
            const res = await fetch(`${API_BASE_URL}/chatbot/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg, history }),
            });
            const data = await res.json();
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.answer,
                results: data.results || [],
                result_type: data.result_type || 'none',
                timestamp: new Date().toISOString(),
            }]);
        } catch (e) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.',
                results: [],
                result_type: 'none',
                timestamp: new Date().toISOString(),
            }]);
        } finally {
            setLoading(false);
        }
    };

    const QUICK_ACTIONS = [
        "Today's alerts", "High risk events", "System overview",
        "Find fights", "Alerts last hour", "Critical incidents",
    ];

    return (
        <>
            {/* Floating button */}
            <Tooltip title="Surveillance Assistant" placement="left">
                <Box
                    onClick={() => setOpen(o => !o)}
                    sx={{
                        position: 'fixed', bottom: 24, right: 24, zIndex: 1300,
                        width: 52, height: 52, borderRadius: '50%',
                        bgcolor: 'primary.main', color: '#fff',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        cursor: 'pointer', boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
                        transition: 'transform 0.2s',
                        '&:hover': { transform: 'scale(1.08)' },
                    }}
                >
                    {open ? <X size={22} /> : <MessageSquare size={22} />}
                    {!open && messages.length > 1 && (
                        <Box sx={{
                            position: 'absolute', top: -2, right: -2,
                            width: 16, height: 16, borderRadius: '50%',
                            bgcolor: '#ef4444', fontSize: '0.6rem',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            color: '#fff', fontWeight: 700,
                        }}>
                            {Math.min(messages.length - 1, 9)}
                        </Box>
                    )}
                </Box>
            </Tooltip>

            {/* Chat window */}
            <Fade in={open}>
                <Paper
                    elevation={8}
                    sx={{
                        position: 'fixed', bottom: 88, right: 24, zIndex: 1299,
                        width: { xs: 'calc(100vw - 48px)', sm: 400 },
                        height: 560, display: 'flex', flexDirection: 'column',
                        borderRadius: 3, overflow: 'hidden',
                        border: `1px solid ${theme.palette.divider}`,
                    }}
                >
                    {/* Header */}
                    <Box sx={{
                        px: 2, py: 1.5, bgcolor: 'primary.main', color: '#fff',
                        display: 'flex', alignItems: 'center', gap: 1.5,
                    }}>
                        <Avatar sx={{ width: 32, height: 32, bgcolor: alpha('#fff', 0.2) }}>
                            <Bot size={16} />
                        </Avatar>
                        <Box sx={{ flex: 1 }}>
                            <Typography variant="subtitle2" sx={{ fontWeight: 700, lineHeight: 1 }}>
                                AURORA Assistant
                            </Typography>
                            <Typography variant="caption" sx={{ opacity: 0.8 }}>
                                Surveillance Intelligence
                            </Typography>
                        </Box>
                        <IconButton size="small" onClick={() => setOpen(false)} sx={{ color: '#fff' }}>
                            <X size={16} />
                        </IconButton>
                    </Box>

                    {/* Messages */}
                    <Box sx={{ flex: 1, overflowY: 'auto', p: 2, bgcolor: alpha(theme.palette.background.default, 0.5) }}>
                        {messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)}
                        {loading && (
                            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 1 }}>
                                <Avatar sx={{ width: 28, height: 28, bgcolor: 'primary.main' }}>
                                    <Bot size={14} />
                                </Avatar>
                                <Paper sx={{ p: 1.5, borderRadius: '12px 12px 12px 2px', border: `1px solid ${theme.palette.divider}` }}>
                                    <CircularProgress size={14} />
                                </Paper>
                            </Box>
                        )}
                        <div ref={messagesEndRef} />
                    </Box>

                    {/* Quick actions */}
                    {messages.length <= 1 && (
                        <Box sx={{ px: 2, pb: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                            {QUICK_ACTIONS.map(a => (
                                <Chip key={a} label={a} size="small" clickable onClick={() => sendMessage(a)}
                                    sx={{ fontSize: '0.65rem', height: 22 }} />
                            ))}
                        </Box>
                    )}

                    {/* Suggestions */}
                    {suggestions.length > 0 && (
                        <Paper variant="outlined" sx={{ mx: 2, mb: 0.5, borderRadius: 1, overflow: 'hidden' }}>
                            {suggestions.map((s, i) => (
                                <Box key={i} onClick={() => { setInput(s); setSuggestions([]); inputRef.current?.focus(); }}
                                    sx={{ px: 1.5, py: 0.75, cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' },
                                        borderBottom: i < suggestions.length - 1 ? `1px solid ${theme.palette.divider}` : 'none' }}>
                                    <Typography variant="caption">{s}</Typography>
                                </Box>
                            ))}
                        </Paper>
                    )}

                    {/* Input */}
                    <Box sx={{ p: 1.5, borderTop: `1px solid ${theme.palette.divider}`, display: 'flex', gap: 1 }}>
                        <TextField
                            inputRef={inputRef}
                            fullWidth
                            size="small"
                            placeholder="Ask about alerts, incidents..."
                            value={input}
                            onChange={e => { setInput(e.target.value); fetchSuggestions(e.target.value); }}
                            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                            disabled={loading}
                            sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2, fontSize: '0.85rem' } }}
                        />
                        <IconButton
                            onClick={() => sendMessage()}
                            disabled={loading || !input.trim()}
                            color="primary"
                            sx={{ bgcolor: 'primary.main', color: '#fff', borderRadius: 2, width: 38, height: 38,
                                '&:hover': { bgcolor: 'primary.dark' }, '&:disabled': { bgcolor: 'action.disabledBackground' } }}
                        >
                            <Send size={16} />
                        </IconButton>
                    </Box>
                </Paper>
            </Fade>
        </>
    );
}
