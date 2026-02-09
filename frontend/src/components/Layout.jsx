import React, { useState } from 'react';
import { Box, AppBar, Toolbar, Typography, IconButton, Container, Button, useTheme, Avatar, Tooltip, Drawer, List, ListItem, ListItemIcon, ListItemText, Popover, Menu, MenuItem, Divider } from '@mui/material';
import { Menu as MenuIcon, LayoutDashboard, Video, BarChart2, AlertCircle, Settings, ShieldCheck, Bell, ChevronDown, LogOut, FileVideo, User, Mail } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';

const Layout = ({ children }) => {
    const theme = useTheme();
    const navigate = useNavigate();
    const location = useLocation();
    const [mobileOpen, setMobileOpen] = useState(false);
    const [notificationAnchor, setNotificationAnchor] = useState(null);
    const [profileAnchor, setProfileAnchor] = useState(null);

    const menuItems = [
        { text: 'Dashboard', icon: <LayoutDashboard size={18} />, path: '/' },
        { text: 'Surveillance', icon: <Video size={18} />, path: '/surveillance' },
        { text: 'Intelligence', icon: <BarChart2 size={18} />, path: '/intelligence' },
        { text: 'Archives', icon: <FileVideo size={18} />, path: '/archives' },
        { text: 'Alerts', icon: <AlertCircle size={18} />, path: '/alerts' },
        { text: 'System', icon: <Settings size={18} />, path: '/system' },
    ];

    const handleNotificationClick = (event) => {
        setNotificationAnchor(event.currentTarget);
    };

    const handleNotificationClose = () => {
        setNotificationAnchor(null);
    };

    const handleProfileClick = (event) => {
        setProfileAnchor(event.currentTarget);
    };

    const handleProfileClose = () => {
        setProfileAnchor(null);
    };

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
                            <MenuIcon />
                        </IconButton>

                        {/* Branding */}
                        <Box
                            onClick={() => navigate('/')}
                            sx={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 1.5,
                                mr: 4,
                                cursor: 'pointer',
                                '&:hover': {
                                    opacity: 0.85
                                },
                                transition: 'opacity 0.2s ease'
                            }}
                        >
                            <img
                                src="/logo.jpeg"
                                alt="Aurora Sentinel Logo"
                                style={{
                                    width: 40,
                                    height: 40,
                                    borderRadius: '10px',
                                    objectFit: 'cover'
                                }}
                            />
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
                            <Tooltip title="Notifications">
                                <IconButton
                                    size="small"
                                    sx={{ color: theme.palette.text.secondary }}
                                    onClick={handleNotificationClick}
                                >
                                    <Bell size={20} />
                                </IconButton>
                            </Tooltip>

                            {/* Notification Popover */}
                            <Popover
                                open={Boolean(notificationAnchor)}
                                anchorEl={notificationAnchor}
                                onClose={handleNotificationClose}
                                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                                transformOrigin={{ vertical: 'top', horizontal: 'right' }}
                                PaperProps={{
                                    sx: {
                                        mt: 1.5,
                                        borderRadius: 3,
                                        minWidth: 280,
                                        boxShadow: '0 10px 40px rgba(0,0,0,0.1)'
                                    }
                                }}
                            >
                                <Box sx={{ p: 2.5 }}>
                                    <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>Notifications</Typography>
                                    <Divider sx={{ mb: 2 }} />
                                    <Box sx={{
                                        py: 4,
                                        textAlign: 'center',
                                        color: theme.palette.text.secondary
                                    }}>
                                        <Bell size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
                                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                            No new notifications
                                        </Typography>
                                    </Box>
                                </Box>
                            </Popover>

                            <Button
                                color="inherit"
                                startIcon={
                                    <Avatar sx={{
                                        width: 32,
                                        height: 32,
                                        background: 'linear-gradient(135deg, #6F8F72 0%, #4a6b4d 100%)',
                                        fontSize: '0.75rem',
                                        fontWeight: 700,
                                        letterSpacing: '0.05em',
                                        boxShadow: '0 2px 8px rgba(111, 143, 114, 0.3)'
                                    }}>
                                        OP
                                    </Avatar>
                                }
                                endIcon={<ChevronDown size={16} />}
                                onClick={handleProfileClick}
                                sx={{
                                    textTransform: 'none',
                                    color: theme.palette.text.primary,
                                    fontWeight: 600,
                                    ml: 1,
                                    px: 2,
                                    py: 1,
                                    borderRadius: 2,
                                    '&:hover': {
                                        bgcolor: 'rgba(111, 143, 114, 0.08)'
                                    }
                                }}
                            >
                                Operator
                            </Button>

                            {/* Profile Menu */}
                            <Menu
                                anchorEl={profileAnchor}
                                open={Boolean(profileAnchor)}
                                onClose={handleProfileClose}
                                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                                transformOrigin={{ vertical: 'top', horizontal: 'right' }}
                                PaperProps={{
                                    sx: {
                                        mt: 1.5,
                                        borderRadius: 3,
                                        minWidth: 200,
                                        boxShadow: '0 10px 40px rgba(0,0,0,0.1)'
                                    }
                                }}
                            >
                                <Box sx={{ px: 2, py: 1.5, borderBottom: `1px solid ${theme.palette.divider}` }}>
                                    <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Operator</Typography>
                                    <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>operator@aurora.local</Typography>
                                </Box>
                                <MenuItem onClick={handleProfileClose} sx={{ py: 1.5, gap: 1.5 }}>
                                    <User size={18} />
                                    <Typography variant="body2">Profile</Typography>
                                </MenuItem>
                                <MenuItem onClick={handleProfileClose} sx={{ py: 1.5, gap: 1.5 }}>
                                    <Settings size={18} />
                                    <Typography variant="body2">Settings</Typography>
                                </MenuItem>
                                <Divider />
                                <MenuItem onClick={handleProfileClose} sx={{ py: 1.5, gap: 1.5, color: theme.palette.error.main }}>
                                    <LogOut size={18} />
                                    <Typography variant="body2">Logout</Typography>
                                </MenuItem>
                            </Menu>
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
        </Box >
    );
};

export default Layout;
