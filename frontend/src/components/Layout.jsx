import React, { useState } from 'react';
import { Box, AppBar, Toolbar, Typography, IconButton, Container, Button, useTheme, Avatar, Tooltip, Drawer, List, ListItem, ListItemIcon, ListItemText, Menu as MuiMenu, MenuItem, Badge, Popover } from '@mui/material';
import { Menu, LayoutDashboard, Video, BarChart2, AlertCircle, Settings, ShieldCheck, Bell, ChevronDown, LogOut, Search, FileVideo, Info, ShieldAlert, User } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';
import logoImage from '../assets/logo.png';
import { format } from 'date-fns';
import { useAuth } from '../context/AuthContext';

const Layout = ({ children }) => {
    const theme = useTheme();
    const navigate = useNavigate();
    const location = useLocation();
    const { user, logout } = useAuth();
    const [mobileOpen, setMobileOpen] = useState(false);
    const [anchorEl, setAnchorEl] = useState(null);
    const [profileAnchor, setProfileAnchor] = useState(null);
    const [notifications, setNotifications] = useState([
        { id: 1, title: 'Loitering Detected', time: new Date(), level: 'Warning' },
        { id: 2, title: 'Unauthorized Entry', time: new Date(Date.now() - 1000 * 60 * 5), level: 'Critical' },
        { id: 3, title: 'Camera 04 Offline', time: new Date(Date.now() - 1000 * 60 * 15), level: 'Info' }
    ]);

    const handleNotifClick = (event) => setAnchorEl(event.currentTarget);
    const handleNotifClose = () => setAnchorEl(null);
    const openNotif = Boolean(anchorEl);

    const handleProfileClick = (event) => setProfileAnchor(event.currentTarget);
    const handleProfileClose = () => setProfileAnchor(null);
    const handleLogout = () => {
        handleProfileClose();
        logout();
        navigate('/login');
    };

    const menuItems = [
        { text: 'Dashboard', icon: <LayoutDashboard size={18} />, path: '/', roles: ['operator', 'admin'] },
        { text: 'Admin Panel', icon: <ShieldAlert size={18} />, path: '/admin', roles: ['admin'] },
        { text: 'Surveillance', icon: <Video size={18} />, path: '/surveillance', roles: ['operator', 'admin'] },
        { text: 'Intelligence', icon: <BarChart2 size={18} />, path: '/intelligence', roles: ['operator', 'admin'] },
        { text: 'Archives', icon: <FileVideo size={18} />, path: '/archives', roles: ['operator', 'admin'] },
        { text: 'Alerts', icon: <AlertCircle size={18} />, path: '/alerts', roles: ['operator', 'admin'] },
        { text: 'System', icon: <Settings size={18} />, path: '/system', roles: ['operator', 'admin'] },
    ].filter(item => item.roles.includes(user?.role || 'operator'));

    return (
        <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', bgcolor: 'background.default' }}>

            {/* --- Level 1: Brand & Utilities Header --- */}
            <AppBar
                position="static"
                elevation={0}
                sx={{
                    bgcolor: 'rgba(255, 255, 255, 0.85)',
                    backdropFilter: 'blur(12px)',
                    borderBottom: `1px solid ${theme.palette.divider}`,
                    zIndex: (theme) => theme.zIndex.appBar
                }}
            >
                <Container maxWidth="xl">
                    <Toolbar disableGutters sx={{ height: 64, position: 'relative' }}>

                        {/* Left Section: Mobile Menu & Notifications */}
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <IconButton
                                color="inherit"
                                edge="start"
                                onClick={() => setMobileOpen(true)}
                                sx={{ mr: 1, display: { md: 'none' }, color: theme.palette.text.secondary }}
                            >
                                <Menu />
                            </IconButton>

                            <Tooltip title="Notifications">
                                <IconButton
                                    size="small"
                                    onClick={handleNotifClick}
                                    sx={{
                                        color: theme.palette.text.secondary,
                                        mr: 2,
                                        '&:hover': { color: theme.palette.primary.main }
                                    }}
                                >
                                    <Badge badgeContent={notifications.length} color="error" variant="dot">
                                        <Bell size={20} />
                                    </Badge>
                                </IconButton>
                            </Tooltip>

                            <Popover
                                open={openNotif}
                                anchorEl={anchorEl}
                                onClose={handleNotifClose}
                                anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
                                transformOrigin={{ vertical: 'top', horizontal: 'left' }}
                                PaperProps={{
                                    sx: { width: 320, mt: 1.5, borderRadius: 2, boxShadow: '0 8px 32px rgba(0,0,0,0.12)' }
                                }}
                            >
                                <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Notifications</Typography>
                                    <Badge badgeContent={notifications.length} color="primary" sx={{ '& .MuiBadge-badge': { fontSize: 10, height: 18, minWidth: 18 } }} />
                                </Box>
                                <List sx={{ p: 0, maxHeight: 400, overflow: 'auto' }}>
                                    {notifications.map((n) => (
                                        <MenuItem key={n.id} onClick={handleNotifClose} sx={{ py: 1.5, borderBottom: `1px solid ${theme.palette.divider}`, '&:last-child': { borderBottom: 0 } }}>
                                            <Box sx={{ display: 'flex', gap: 2, width: '100%' }}>
                                                <Box sx={{
                                                    p: 1,
                                                    borderRadius: '50%',
                                                    bgcolor: n.level === 'Critical' ? '#FEF2F2' : n.level === 'Warning' ? '#FFF7ED' : '#F0F9FF',
                                                    display: 'flex'
                                                }}>
                                                    <AlertCircle size={16} color={n.level === 'Critical' ? '#EF4444' : n.level === 'Warning' ? '#F97316' : '#0EA5E9'} />
                                                </Box>
                                                <Box sx={{ flexGrow: 1 }}>
                                                    <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.85rem' }}>{n.title}</Typography>
                                                    <Typography variant="caption" color="text.secondary">{n.level} • {format(n.time, 'HH:mm')}</Typography>
                                                </Box>
                                            </Box>
                                        </MenuItem>
                                    ))}
                                </List>
                            </Popover>
                        </Box>

                        {/* Center Section: Branding */}
                        <Box sx={{
                            position: 'absolute',
                            left: '50%',
                            transform: 'translateX(-50%)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1.5,
                            pointerEvents: 'none'
                        }}>
                            <Box
                                component="img"
                                src={logoImage}
                                alt="Aurora Sentinel"
                                sx={{ width: 40, height: 40, objectFit: 'contain', borderRadius: '8px' }}
                            />
                            <Box sx={{ pointerEvents: 'auto', cursor: 'pointer' }} onClick={() => navigate('/')}>
                                <Typography variant="h6" sx={{
                                    lineHeight: 1,
                                    color: theme.palette.text.primary,
                                    letterSpacing: '-0.02em',
                                    fontWeight: 900,
                                    fontSize: '1.2rem',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '2px'
                                }}>
                                    AURORA<span style={{ fontWeight: 400, color: theme.palette.primary.main }}>SENTINEL</span>
                                </Typography>
                            </Box>
                        </Box>

                        {/* Right Section: Profile */}
                        <Box sx={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Box sx={{ width: 1, height: 24, bgcolor: '#fafafa', mx: 1.5 }} />

                            <Button
                                color="inherit"
                                onClick={handleProfileClick}
                                startIcon={<Avatar sx={{ width: 32, height: 32, bgcolor: user?.role === 'admin' ? theme.palette.secondary.main : theme.palette.primary.main, fontSize: '0.9rem', fontWeight: 700 }}>{user?.role === 'admin' ? 'AD' : 'OP'}</Avatar>}
                                endIcon={<ChevronDown size={16} />}
                                sx={{
                                    textTransform: 'none', px: 1, py: 0.5, borderRadius: '12px', color: theme.palette.text.primary, fontWeight: 600,
                                    '&:hover': { bgcolor: 'rgba(111, 143, 114, 0.08)' }
                                }}
                            >
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                                    <Typography variant="body2" sx={{ fontWeight: 700 }}>{user?.name || 'Operator'}</Typography>
                                    <Badge
                                        badgeContent={user?.id || 'OP-4921'}
                                        sx={{
                                            '& .MuiBadge-badge': {
                                                bgcolor: user?.role === 'admin' ? theme.palette.secondary.main : theme.palette.primary.main,
                                                color: 'white', fontSize: '0.65rem', height: 18, width: '4.31em', padding: '0 4px', fontWeight: 800, position: 'static', transform: 'none'
                                            }
                                        }}
                                    />
                                </Box>
                            </Button>

                            <MuiMenu
                                anchorEl={profileAnchor}
                                open={Boolean(profileAnchor)}
                                onClose={handleProfileClose}
                                PaperProps={{ sx: { mt: 1, width: 200, borderRadius: 3, boxShadow: '0 10px 25px rgba(0,0,0,0.1)' } }}
                            >
                                <MenuItem onClick={() => { handleProfileClose(); navigate('/system'); }}>
                                    <ListItemIcon><User size={18} /></ListItemIcon>
                                    <ListItemText primary="Profile Settings" />
                                </MenuItem>
                                {user?.role === 'admin' && (
                                    <MenuItem onClick={() => { handleProfileClose(); navigate('/admin'); }}>
                                        <ListItemIcon><ShieldCheck size={18} /></ListItemIcon>
                                        <ListItemText primary="Admin Panel" />
                                    </MenuItem>
                                )}
                                <Box sx={{ my: 1, borderTop: `1px solid ${theme.palette.divider}` }} />
                                <MenuItem onClick={handleLogout} sx={{ color: 'error.main' }}>
                                    <ListItemIcon><LogOut size={18} color={theme.palette.error.main} /></ListItemIcon>
                                    <ListItemText primary="Terminate Session" />
                                </MenuItem>
                            </MuiMenu>
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
