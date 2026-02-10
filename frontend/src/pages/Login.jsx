import React, { useState } from 'react';
import { Box, Paper, Typography, TextField, Button, IconButton, InputAdornment, Container, Tab, Tabs, alpha, useTheme } from '@mui/material';
import { Shield, Eye, EyeOff, Lock, User, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import logoImage from '../assets/logo.png';

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
            bgcolor: theme.palette.background.default, // Light Beige
            position: 'relative',
            overflow: 'hidden'
        }}>
            {/* Soft Ambient Background Elements */}
            <Box sx={{
                position: 'absolute',
                width: '800px',
                height: '800px',
                borderRadius: '50%',
                bgcolor: alpha(theme.palette.primary.main, 0.08),
                filter: 'blur(120px)',
                top: '-300px',
                right: '-300px',
                zIndex: 0
            }} />
            <Box sx={{
                position: 'absolute',
                width: '600px',
                height: '600px',
                borderRadius: '50%',
                bgcolor: alpha(theme.palette.secondary.main, 0.05),
                filter: 'blur(100px)',
                bottom: '-200px',
                left: '-200px',
                zIndex: 0
            }} />

            <Container maxWidth="xs" sx={{ position: 'relative', zIndex: 1 }}>
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.6 }}
                >
                    <Box sx={{ textAlign: 'center', mb: 5 }}>
                        <Box sx={{
                            display: 'inline-flex',
                            p: 1.5,
                            borderRadius: '24px',
                            bgcolor: '#FFFFFF',
                            mb: 2.5,
                            boxShadow: '0 8px 32px rgba(111, 143, 114, 0.15)',
                            border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`
                        }}>
                            <Box
                                component="img"
                                src={logoImage}
                                alt="Logo"
                                sx={{ width: 60, height: 60, objectFit: 'contain' }}
                            />
                        </Box>
                        <Typography variant="h3" sx={{
                            fontWeight: 900,
                            color: theme.palette.text.primary,
                            letterSpacing: '-0.04em',
                            fontSize: '2.5rem'
                        }}>
                            AURORA<span style={{ fontWeight: 400, color: theme.palette.primary.main }}>SENTINEL</span>
                        </Typography>
                        <Typography variant="subtitle1" sx={{ color: theme.palette.text.secondary, mt: 1, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', fontSize: '0.8rem' }}>
                            Urban Intelligence Protocol
                        </Typography>
                    </Box>

                    <Paper sx={{
                        p: 4.5,
                        borderRadius: 8,
                        bgcolor: 'rgba(255, 255, 255, 0.8)',
                        backdropFilter: 'blur(24px)',
                        border: '1px solid #FFFFFF',
                        boxShadow: '0 32px 64px -16px rgba(44, 51, 51, 0.12)',
                        transition: 'all 0.3s ease'
                    }}>
                        <Tabs
                            value={role}
                            onChange={handleRoleChange}
                            centered
                            sx={{
                                mb: 5,
                                '& .MuiTabs-indicator': { height: 4, borderRadius: '4px 4px 0 0', bgcolor: theme.palette.primary.main },
                                '& .MuiTab-root': { color: theme.palette.text.secondary, fontWeight: 800, textTransform: 'none', fontSize: '1.05rem', minWidth: 120 },
                                '& .Mui-selected': { color: theme.palette.primary.main }
                            }}
                        >
                            <Tab label="Operator" value="operator" />
                            <Tab label="Admin" value="admin" />
                        </Tabs>

                        <form onSubmit={handleSubmit}>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3.5 }}>
                                <TextField
                                    fullWidth
                                    label="Personnel ID"
                                    placeholder={role === 'admin' ? 'ADM-XXXX' : 'OP-XXXX'}
                                    variant="outlined"
                                    InputProps={{
                                        startAdornment: (
                                            <InputAdornment position="start">
                                                <User size={20} color={theme.palette.primary.main} />
                                            </InputAdornment>
                                        ),
                                        sx: {
                                            borderRadius: 4,
                                            bgcolor: '#FFFFFF',
                                            '& fieldset': { borderColor: alpha(theme.palette.divider, 0.5) },
                                            '&:hover fieldset': { borderColor: theme.palette.primary.main },
                                            fontWeight: 600
                                        }
                                    }}
                                />
                                <TextField
                                    fullWidth
                                    label="Security Key"
                                    type={showPassword ? 'text' : 'password'}
                                    variant="outlined"
                                    InputProps={{
                                        startAdornment: (
                                            <InputAdornment position="start">
                                                <Lock size={20} color={theme.palette.primary.main} />
                                            </InputAdornment>
                                        ),
                                        endAdornment: (
                                            <InputAdornment position="end">
                                                <IconButton onClick={() => setShowPassword(!showPassword)} edge="end" sx={{ color: theme.palette.text.secondary }}>
                                                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                                </IconButton>
                                            </InputAdornment>
                                        ),
                                        sx: {
                                            borderRadius: 4,
                                            bgcolor: '#FFFFFF',
                                            '& fieldset': { borderColor: alpha(theme.palette.divider, 0.5) },
                                            '&:hover fieldset': { borderColor: theme.palette.primary.main },
                                            fontWeight: 600
                                        }
                                    }}
                                />

                                <Button
                                    fullWidth
                                    type="submit"
                                    variant="contained"
                                    size="large"
                                    endIcon={<ArrowRight size={22} />}
                                    sx={{
                                        py: 2.25,
                                        borderRadius: 4,
                                        fontWeight: 900,
                                        fontSize: '1.15rem',
                                        mt: 2,
                                        boxShadow: `0 12px 24px ${alpha(theme.palette.primary.main, 0.25)}`,
                                        '&:hover': {
                                            transform: 'translateY(-2px)',
                                            bgcolor: theme.palette.primary.dark,
                                            boxShadow: `0 16px 32px ${alpha(theme.palette.primary.main, 0.35)}`
                                        },
                                        transition: 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
                                    }}
                                >
                                    Establish Link
                                </Button>
                            </Box>
                        </form>
                    </Paper>

                    <Box sx={{ mt: 5, textAlign: 'center' }}>
                        <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 800, letterSpacing: '0.2em' }}>
                            AURORA SENTINEL v2.0.5 <span style={{ color: theme.palette.secondary.main }}>PRO</span>
                        </Typography>
                    </Box>
                </motion.div>
            </Container>
        </Box>
    );
};

export default Login;
