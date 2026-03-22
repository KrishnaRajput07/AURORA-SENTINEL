import React, { useState, useEffect, useRef } from 'react';
import { Box, Paper, Typography, TextField, Button, IconButton, InputAdornment, Container, Tab, Tabs, alpha, useTheme, CircularProgress } from '@mui/material';
import { Shield, Eye, EyeOff, Lock, User, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import mascotImage from '../assets/mascot_transparent.png';
import { API_BASE_URL } from '../config';

const Login = () => {
    const theme = useTheme();
    const { login, verifyOperator } = useAuth();
    const navigate = useNavigate();
    const [role, setRole] = useState('operator');
    const [showPassword, setShowPassword] = useState(false);
    const [credentials, setCredentials] = useState({ id: '', password: '' });
    const [loading, setLoading] = useState(false);

    // Mouse position for left pane interaction and 3D tilt
    const mouseX = useMotionValue(500);
    const mouseY = useMotionValue(300);
    
    // Smooth springs for spotlight and tilt
    const springX = useSpring(mouseX, { stiffness: 100, damping: 30 });
    const springY = useSpring(mouseY, { stiffness: 100, damping: 30 });
    
    // Spotlight position
    const spotlightX = useTransform(springX, (x) => `${x}px`);
    const spotlightY = useTransform(springY, (y) => `${y}px`);

    const handleMouseMove = (e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // Map center to 0,0 for easier rotation calc
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        mouseX.set(x - centerX);
        mouseY.set(y - centerY);
    };

    const handleMouseLeave = () => {
        mouseX.set(0);
        mouseY.set(0);
    };

    const handleRoleChange = (event, newValue) => {
        setRole(newValue);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        // Artificial delay for premium feel
        await new Promise(resolve => setTimeout(resolve, 1000));

        if (role === 'admin') {
            if (credentials.id === 'ADM-123' && credentials.password === '0000') {
                login(role, { id: 'ADM-123', name: 'System Administrator' });
                navigate('/admin');
            } else {
                alert('Authorization revoked: Invalid Admin Credentials');
                setLoading(false);
            }
        } else {
            // Check Maintenance Mode for Operators
            try {
                const maintenanceResponse = await fetch(`${API_BASE_URL}/settings/maintenance`);
                const maintenanceData = await maintenanceResponse.json();
                
                if (maintenanceData.maintenance_mode) {
                    alert('SYSTEM MAINTENANCE: Maintenance is under progress. Operators cannot log in at this time. Please contact your administrator.');
                    setLoading(false);
                    return;
                }
            } catch (error) {
                console.error('Error checking maintenance mode:', error);
            }

            const operator = verifyOperator(credentials.id, credentials.password);
            if (operator) {
                login(role, { id: operator.id, name: operator.name });
                navigate('/');
            } else {
                alert('Authorization revoked: Invalid Operator Credentials');
                setLoading(false);
            }
        }
    };

    return (
        <Box 
            sx={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                bgcolor: '#DED7C7',
                position: 'relative',
                overflow: 'hidden',
            }}
        >
            {/* Page Background Animation */}
            <Box sx={{
                position: 'absolute',
                inset: 0,
                zIndex: 0,
                opacity: 0.3,
                filter: 'blur(100px)',
                background: `radial-gradient(circle at 10% 10%, ${theme.palette.primary.main} 0%, transparent 40%),
                            radial-gradient(circle at 90% 90%, ${theme.palette.secondary.main} 0%, transparent 40%),
                            radial-gradient(circle at 50% 50%, #61745E 0%, transparent 50%)`,
                animation: 'pulseBg 15s infinite alternate ease-in-out',
                '@keyframes pulseBg': {
                    '0%': { transform: 'scale(1) rotate(0deg)' },
                    '100%': { transform: 'scale(1.2) rotate(10deg)' },
                }
            }} />

            <motion.div
                onMouseMove={handleMouseMove}
                onMouseLeave={handleMouseLeave}
                style={{ 
                    zIndex: 1, 
                    width: '100%', 
                    maxWidth: '1050px', 
                    padding: '20px',
                }}
            >
                <Paper sx={{
                    display: 'flex',
                    flexDirection: { xs: 'column', md: 'row' },
                    overflow: 'hidden',
                    borderRadius: '40px',
                    minHeight: '620px',
                    boxShadow: '0 50px 100px -20px rgba(0,0,0,0.25), 0 0 0 1px rgba(255,255,255,0.3)',
                    position: 'relative',
                    bgcolor: 'rgba(255, 255, 255, 0.7)',
                    backdropFilter: 'blur(30px)',
                    // "Aurora" Card Animation
                    '&::before': {
                        content: '""',
                        position: 'absolute',
                        inset: 0,
                        zIndex: -1,
                        background: 'linear-gradient(45deg, rgba(111, 143, 114, 0.05), rgba(242, 166, 90, 0.05))',
                        animation: 'aurora 10s infinite linear alternate',
                    },
                    '@keyframes aurora': {
                        '0%': { backgroundPosition: '0% 50%' },
                        '100%': { backgroundPosition: '100% 50%' },
                    }
                }}>
                    
                    {/* Left Pane: Welcome Section */}
                    <Box 
                        sx={{
                            flex: 1.1,
                            bgcolor: '#61745E', 
                            color: '#FFFFFF',
                            p: 6,
                            display: 'flex',
                            flexDirection: 'column',
                            justifyContent: 'center',
                            alignItems: 'center',
                            position: 'relative',
                            overflow: 'hidden',
                            textAlign: 'center',
                            // Mesh/Grain Texture
                            '&::after': {
                                content: '""',
                                position: 'absolute',
                                inset: 0,
                                opacity: 0.1,
                                backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
                                pointerEvents: 'none'
                            }
                        }}
                    >
                        {/* Interactive Spotlight */}
                        <motion.div style={{
                            position: 'absolute',
                            width: '800px',
                            height: '800px',
                            background: 'radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 60%)',
                            left: spotlightX,
                            top: spotlightY,
                            transform: 'translate(-50%, -50%)',
                            pointerEvents: 'none',
                            zIndex: 1
                        }} />

                        <Box sx={{ position: 'relative', zIndex: 2, mb: 2 }}>
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={role}
                                    initial={{ y: 40, opacity: 0, filter: 'blur(10px)' }}
                                    animate={{ y: 0, opacity: 1, filter: 'blur(0px)' }}
                                    exit={{ y: -40, opacity: 0, filter: 'blur(10px)' }}
                                    transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                                >
                                    <Typography variant="h2" sx={{ fontWeight: 900, mb: 1.5, letterSpacing: '-0.04em', textShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                                        Welcome {role === 'operator' ? 'Operator' : 'Admin'}!
                                    </Typography>
                                    <Typography variant="h6" sx={{ opacity: 0.9, fontWeight: 400, maxWidth: '300px', mx: 'auto', lineHeight: 1.4 }}>
                                        Secure access to Aurora Sentinel Intelligence Protocol.
                                    </Typography>
                                </motion.div>
                            </AnimatePresence>
                        </Box>

                        <motion.div
                            animate={{ 
                                y: [0, -15, 0],
                                rotate: [0, 1, -1, 0]
                            }}
                            transition={{ 
                                duration: 6, 
                                repeat: Infinity, 
                                ease: "easeInOut" 
                            }}
                            style={{ position: 'relative', zIndex: 2 }}
                        >
                            <Box 
                                component="img"
                                src={mascotImage}
                                alt="Mascot"
                                sx={{ 
                                    width: { xs: 200, md: 280 }, 
                                    height: 'auto',
                                    filter: 'drop-shadow(0 20px 40px rgba(0,0,0,0.3))',
                                }}
                            />
                        </motion.div>
                    </Box>

                    {/* Right Pane: Sign In Section */}
                    <Box sx={{
                        flex: 1,
                        p: { xs: 4, md: 8 },
                        bgcolor: '#FAF7F0',
                        display: 'flex',
                        flexDirection: 'column',
                        position: 'relative',
                        zIndex: 2,
                    }}>
                        <Typography variant="h3" sx={{ fontWeight: 950, mb: 1, color: '#1A1A1A', letterSpacing: '-0.05em' }}>
                            Sign In
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#666', mb: 4, fontWeight: 500 }}>
                            Enter your credentials to establish a secure link.
                        </Typography>

                        <Tabs
                            value={role}
                            onChange={handleRoleChange}
                            sx={{
                                mb: 5,
                                pl: 0.5, // Slight offset to prevent clipping on scale
                                '& .MuiTabs-indicator': { height: 4, borderRadius: 2, bgcolor: '#61745E' },
                                '& .MuiTabs-scroller': { overflow: 'visible' },
                                '& .MuiTab-root': { 
                                    color: '#AAA', 
                                    fontWeight: 800, 
                                    fontSize: '1.2rem', 
                                    textTransform: 'none', 
                                    px: 0,
                                    mr: 4,
                                    minWidth: 'auto',
                                    transition: 'all 0.3s ease',
                                    transformOrigin: 'center left',
                                    '&.Mui-selected': { color: '#61745E', transform: 'scale(1.1)' }
                                }
                            }}
                        >
                            <Tab label="Operator" value="operator" />
                            <Tab label="Admin" value="admin" />
                        </Tabs>

                        <form onSubmit={handleSubmit} style={{ width: '100%' }}>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <Box>
                                    <Typography variant="caption" sx={{ fontWeight: 900, color: '#444', mb: 1.5, display: 'block', textTransform: 'uppercase', letterSpacing: '0.15em', fontSize: '0.7rem' }}>
                                        Personnel ID
                                    </Typography>
                                    <TextField
                                        fullWidth
                                        placeholder={role === 'admin' ? 'ADM-XXXX' : 'OP-XXXX'}
                                        variant="outlined"
                                        value={credentials.id}
                                        onChange={(e) => setCredentials({ ...credentials, id: e.target.value })}
                                        InputProps={{
                                            startAdornment: (
                                                <InputAdornment position="start">
                                                    <User size={22} color="#61745E" strokeWidth={2.5} />
                                                </InputAdornment>
                                            ),
                                            sx: {
                                                borderRadius: '16px',
                                                bgcolor: '#FFF',
                                                border: '2px solid rgba(0,0,0,0.03)',
                                                '& fieldset': { border: 'none' },
                                                fontWeight: 700,
                                                fontSize: '1.1rem',
                                                transition: 'all 0.3s ease',
                                                '&:hover, &.Mui-focused': {
                                                    borderColor: '#61745E',
                                                    boxShadow: '0 8px 16px rgba(97, 116, 94, 0.1)'
                                                }
                                            }
                                        }}
                                    />
                                </Box>

                                <Box>
                                    <Typography variant="caption" sx={{ fontWeight: 900, color: '#444', mb: 1.5, display: 'block', textTransform: 'uppercase', letterSpacing: '0.15em', fontSize: '0.7rem' }}>
                                        Security Key
                                    </Typography>
                                    <TextField
                                        fullWidth
                                        type={showPassword ? 'text' : 'password'}
                                        variant="outlined"
                                        value={credentials.password}
                                        onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                                        InputProps={{
                                            startAdornment: (
                                                <InputAdornment position="start">
                                                    <Lock size={22} color="#61745E" strokeWidth={2.5} />
                                                </InputAdornment>
                                            ),
                                            endAdornment: (
                                                <InputAdornment position="end">
                                                    <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                                                        {showPassword ? <EyeOff size={22} /> : <Eye size={22} />}
                                                    </IconButton>
                                                </InputAdornment>
                                            ),
                                            sx: {
                                                borderRadius: '16px',
                                                bgcolor: '#FFF',
                                                border: '2px solid rgba(0,0,0,0.03)',
                                                '& fieldset': { border: 'none' },
                                                fontWeight: 700,
                                                fontSize: '1.1rem',
                                                transition: 'all 0.3s ease',
                                                '&:hover, &.Mui-focused': {
                                                    borderColor: '#61745E',
                                                    boxShadow: '0 8px 16px rgba(97, 116, 94, 0.1)'
                                                }
                                            }
                                        }}
                                    />
                                </Box>

                                <Button
                                    fullWidth
                                    type="submit"
                                    variant="contained"
                                    disabled={loading}
                                    sx={{
                                        py: 2.5,
                                        borderRadius: '18px',
                                        bgcolor: '#61745E',
                                        color: '#fff',
                                        fontWeight: 900,
                                        fontSize: '1.1rem',
                                        textTransform: 'none',
                                        boxShadow: '0 15px 30px rgba(97, 116, 94, 0.3)',
                                        '&:hover': {
                                            bgcolor: '#4d5c4b',
                                            transform: 'translateY(-3px) scale(1.02)',
                                            boxShadow: '0 20px 40px rgba(97, 116, 94, 0.4)',
                                        },
                                        transition: 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
                                    }}
                                >
                                    {loading ? <CircularProgress size={26} sx={{ color: '#fff' }} /> : 'Establish Link'}
                                </Button>
                            </Box>
                        </form>

                        <Box sx={{ mt: 'auto', pt: 6, textAlign: 'center' }}>
                            <Typography variant="caption" sx={{ color: '#999', fontWeight: 800, letterSpacing: '0.2em', fontSize: '0.75rem' }}>
                                AURORA SENTINEL v2.0.5 <span style={{ color: '#61745E' }}>PREMIUM</span>
                            </Typography>
                        </Box>
                    </Box>
                </Paper>
            </motion.div>
        </Box>
    );
};

export default Login;
