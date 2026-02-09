import React, { useState } from 'react';
import { Box, Paper, Typography, TextField, Button, IconButton, InputAdornment, Container, Tab, Tabs, alpha, useTheme } from '@mui/material';
import { Shield, Eye, EyeOff, Lock, User, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const Login = () => {
    const theme = useTheme();
    const { login } = useAuth();
    const navigate = useNavigate();
    const [role, setRole] = useState('operator');
    const [showPassword, setShowPassword] = useState(false);
    const [credentials, setCredentials] = useState({ id: '', password: '' });

    const handleRoleChange = (event, newValue) => setRole(newValue);

    const handleSubmit = (e) => {
        e.preventDefault();
        // Mock login
        login(role);
        navigate(role === 'admin' ? '/admin' : '/');
    };

    return (
        <Box sx={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: '#0f172a',
            position: 'relative',
            overflow: 'hidden'
        }}>
            {/* Animated Background Elements */}
            <Box sx={{
                position: 'absolute',
                width: '600px',
                height: '600px',
                borderRadius: '50%',
                bgcolor: alpha(theme.palette.primary.main, 0.15),
                filter: 'blur(100px)',
                top: '-200px',
                right: '-200px',
                zIndex: 0
            }} />
            <Box sx={{
                position: 'absolute',
                width: '400px',
                height: '400px',
                borderRadius: '50%',
                bgcolor: alpha(theme.palette.secondary.main, 0.1),
                filter: 'blur(80px)',
                bottom: '-100px',
                left: '-100px',
                zIndex: 0
            }} />

            <Container maxWidth="xs" sx={{ position: 'relative', zIndex: 1 }}>
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                >
                    <Box sx={{ textAlign: 'center', mb: 4 }}>
                        <Box sx={{
                            display: 'inline-flex',
                            p: 2,
                            borderRadius: 4,
                            bgcolor: alpha(theme.palette.primary.main, 0.1),
                            mb: 2,
                            border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                        }}>
                            <Shield size={40} color={theme.palette.primary.main} />
                        </Box>
                        <Typography variant="h4" sx={{ fontWeight: 900, color: '#fff', letterSpacing: '-0.02em' }}>
                            AURORA<span style={{ fontWeight: 400, color: theme.palette.primary.main }}>SENTINEL</span>
                        </Typography>
                        <Typography variant="body2" sx={{ color: alpha('#fff', 0.5), mt: 1, fontWeight: 500 }}>
                            Secure Forensic Intelligence Portal
                        </Typography>
                    </Box>

                    <Paper sx={{
                        p: 4,
                        borderRadius: 6,
                        bgcolor: 'rgba(30, 41, 59, 0.7)',
                        backdropFilter: 'blur(20px)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
                    }}>
                        <Tabs
                            value={role}
                            onChange={handleRoleChange}
                            centered
                            sx={{
                                mb: 4,
                                '& .MuiTabs-indicator': { height: 3, borderRadius: '3px 3px 0 0' },
                                '& .MuiTab-root': { color: alpha('#fff', 0.4), fontWeight: 700, textTransform: 'none', fontSize: '1rem' },
                                '& .Mui-selected': { color: theme.palette.primary.main }
                            }}
                        >
                            <Tab label="Operator" value="operator" />
                            <Tab label="Administrator" value="admin" />
                        </Tabs>

                        <form onSubmit={handleSubmit}>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                                <TextField
                                    fullWidth
                                    label="Access ID"
                                    placeholder={role === 'admin' ? 'ADM-XXXX' : 'OP-XXXX'}
                                    variant="outlined"
                                    InputProps={{
                                        startAdornment: (
                                            <InputAdornment position="start">
                                                <User size={20} color={alpha('#fff', 0.5)} />
                                            </InputAdornment>
                                        ),
                                        sx: { color: '#fff', borderRadius: 3, bgcolor: 'rgba(255,255,255,0.05)' }
                                    }}
                                    InputLabelProps={{ sx: { color: alpha('#fff', 0.5) } }}
                                />
                                <TextField
                                    fullWidth
                                    label="Security Key"
                                    type={showPassword ? 'text' : 'password'}
                                    variant="outlined"
                                    InputProps={{
                                        startAdornment: (
                                            <InputAdornment position="start">
                                                <Lock size={20} color={alpha('#fff', 0.5)} />
                                            </InputAdornment>
                                        ),
                                        endAdornment: (
                                            <InputAdornment position="end">
                                                <IconButton onClick={() => setShowPassword(!showPassword)} edge="end" sx={{ color: alpha('#fff', 0.5) }}>
                                                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                                </IconButton>
                                            </InputAdornment>
                                        ),
                                        sx: { color: '#fff', borderRadius: 3, bgcolor: 'rgba(255,255,255,0.05)' }
                                    }}
                                    InputLabelProps={{ sx: { color: alpha('#fff', 0.5) } }}
                                />

                                <Button
                                    fullWidth
                                    type="submit"
                                    variant="contained"
                                    size="large"
                                    endIcon={<ArrowRight size={20} />}
                                    sx={{
                                        py: 2,
                                        borderRadius: 3,
                                        fontWeight: 900,
                                        textTransform: 'none',
                                        fontSize: '1.1rem',
                                        mt: 2,
                                        boxShadow: `0 10px 20px ${alpha(theme.palette.primary.main, 0.3)}`,
                                        '&:hover': { transform: 'translateY(-2px)', boxShadow: `0 15px 30px ${alpha(theme.palette.primary.main, 0.4)}` },
                                        transition: 'all 0.3s ease'
                                    }}
                                >
                                    Initialize Session
                                </Button>
                            </Box>
                        </form>
                    </Paper>

                    <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', mt: 4, color: alpha('#fff', 0.3), fontWeight: 700 }}>
                        AURORA SENTINEL SECURITY v2.0.4 PRO
                    </Typography>
                </motion.div>
            </Container>
        </Box>
    );
};

export default Login;
