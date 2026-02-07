import React, { useState } from 'react';
import { Box, AppBar, Toolbar, Typography, IconButton, Container, Button, useTheme, Avatar, Tooltip, Drawer, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import { Menu, LayoutDashboard, Video, BarChart2, AlertCircle, Settings, ShieldCheck, Bell, ChevronDown, LogOut, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';

const Layout = ({ children }) => {
    const theme = useTheme();
    const navigate = useNavigate();
    const location = useLocation();
    const [mobileOpen, setMobileOpen] = useState(false);

    const menuItems = [
        { text: 'Dashboard', icon: <LayoutDashboard size={18} />, path: '/' },
        { text: 'Surveillance', icon: <Video size={18} />, path: '/surveillance' },
        { text: 'Intelligence', icon: <BarChart2 size={18} />, path: '/analytics' },
        { text: 'Alerts', icon: <AlertCircle size={18} />, path: '/alerts' },
        { text: 'System', icon: <Settings size={18} />, path: '/system' },
    ];

    return (
        <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', bgcolor: 'background.default' }}>

            {/* --- Level 1: Brand & Utilities Header --- */}
            <AppBar position="static" elevation={0} sx={{ bgcolor: '#FFFFFF', borderBottom: `1px solid ${theme.palette.divider}` }}>
                <Container maxWidth="xl">
                    <Toolbar disableGutters sx={{ height: 64 }}>

                        {/* Mobile Menu Icon */}
                        <IconButton
                            color="inherit"
                            edge="start"
                            onClick={() => setMobileOpen(true)}
                            sx={{ mr: 2, display: { md: 'none' }, color: theme.palette.text.secondary }}
                        >
                            <Menu />
                        </IconButton>

                        {/* Branding */}
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mr: 4 }}>
                            <Box sx={{
                                width: 36,
                                height: 36,
                                bgcolor: theme.palette.primary.main,
                                borderRadius: '10px', // Slightly rounded brand logo
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                boxShadow: `0 4px 10px ${theme.palette.action.hover}`
                            }}>
                                <ShieldCheck color="#fff" size={20} />
                            </Box>
                            <Box>
                                <Typography variant="h6" sx={{ lineHeight: 1, color: theme.palette.text.primary, letterSpacing: '-0.01em' }}>
                                    AURORA<span style={{ fontWeight: 400, opacity: 0.8 }}>SENTINEL</span>
                                </Typography>
                            </Box>
                        </Box>

                        {/* Middle Spacer / Search Placeholder */}
                        <Box sx={{ flexGrow: 1 }} />

                        {/* Quick Actions */}
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Tooltip title="Search System">
                                <IconButton size="small" sx={{ color: theme.palette.text.secondary }}>
                                    <Search size={20} />
                                </IconButton>
                            </Tooltip>

                            <Tooltip title="Notifications">
                                <IconButton size="small" sx={{ color: theme.palette.text.secondary }}>
                                    <Bell size={20} />
                                </IconButton>
                            </Tooltip>

                            <Box sx={{ width: 1, height: 24, bgcolor: theme.palette.divider, mx: 1.5 }} />

                            <Button
                                color="inherit"
                                startIcon={<Avatar sx={{ width: 28, height: 28, bgcolor: theme.palette.secondary.main, fontSize: '0.8rem' }}>OP</Avatar>}
                                endIcon={<ChevronDown size={16} />}
                                sx={{
                                    textTransform: 'none',
                                    color: theme.palette.text.primary,
                                    fontWeight: 600
                                }}
                            >
                                Operator
                            </Button>
                        </Box>
                    </Toolbar>
                </Container>
            </AppBar>

            {/* --- Level 2: Centered Navigation Bar --- */}
            <Box sx={{
                bgcolor: '#FFFFFF',
                borderBottom: `1px solid ${theme.palette.divider}`,
                display: { xs: 'none', md: 'block' }
            }}>
                <Container maxWidth="xl">
                    <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1 }}>
                        {menuItems.map((item) => {
                            const isActive = location.pathname === item.path;
                            return (
                                <Box key={item.text} sx={{ position: 'relative', px: 1 }}>
                                    <Button
                                        onClick={() => navigate(item.path)}
                                        startIcon={item.icon}
                                        sx={{
                                            py: 1.5,
                                            px: 3,
                                            borderRadius: '12px', // Rounded pill shape on hover
                                            color: isActive ? theme.palette.primary.main : theme.palette.text.secondary,
                                            fontWeight: isActive ? 700 : 500,
                                            bgcolor: isActive ? 'rgba(111, 143, 114, 0.08)' : 'transparent',
                                            '&:hover': {
                                                bgcolor: 'rgba(111, 143, 114, 0.05)',
                                                color: theme.palette.primary.main
                                            }
                                        }}
                                    >
                                        {item.text}
                                    </Button>
                                    {/* Active Indicator (Small dot instead of full underline for a cleaner look) 
                                    {isActive && (
                                        <motion.div
                                            layoutId="nav-underline"
                                            style={{
                                                position: 'absolute',
                                                bottom: 0,
                                                left: '20%',
                                                right: '20%',
                                                height: 3,
                                                backgroundColor: theme.palette.primary.main,
                                                borderRadius: '3px 3px 0 0'
                                            }}
                                        />
                                    )} */}
                                </Box>
                            )
                        })}
                    </Box>
                </Container>
            </Box>

            {/* --- Mobile Drawer (Hidden on Desktop) --- */}
            <Drawer
                variant="temporary"
                anchor="left"
                open={mobileOpen}
                onClose={() => setMobileOpen(false)}
                sx={{
                    display: { xs: 'block', md: 'none' },
                    '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 280 },
                }}
            >
                <List>
                    <Box sx={{ p: 2, mb: 1 }}>
                        <Typography variant="h6" color="primary">Navigation</Typography>
                    </Box>
                    {menuItems.map((item) => (
                        <ListItem button key={item.text} onClick={() => { navigate(item.path); setMobileOpen(false); }}>
                            <ListItemIcon sx={{ color: theme.palette.primary.main }}>{item.icon}</ListItemIcon>
                            <ListItemText primary={item.text} />
                        </ListItem>
                    ))}
                </List>
            </Drawer>

            {/* --- Main Content Area --- */}
            <Box component="main" sx={{ flexGrow: 1, py: 4 }}>
                <Container maxWidth="xl">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={location.pathname}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            transition={{ duration: 0.2 }}
                        >
                            {children}
                        </motion.div>
                    </AnimatePresence>
                </Container>
            </Box>
        </Box>
    );
};

export default Layout;
