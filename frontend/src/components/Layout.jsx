import React, { useState } from 'react';
import { Box, AppBar, Toolbar, Typography, IconButton, Drawer, List, ListItem, ListItemIcon, ListItemText, useTheme, useMediaQuery, Container } from '@mui/material';
import { Menu, X, LayoutDashboard, AlertTriangle, Video, BarChart2, Settings, Shield, Scan } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';

const DRAWER_WIDTH = 260;

const Layout = ({ children }) => {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));
    const [mobileOpen, setMobileOpen] = useState(false);
    const navigate = useNavigate();
    const location = useLocation();

    const handleDrawerToggle = () => {
        setMobileOpen(!mobileOpen);
    };

    const menuItems = [
        { text: 'Dashboard', icon: <LayoutDashboard size={20} />, path: '/' },
        { text: 'Live Surveillance', icon: <Video size={20} />, path: '/surveillance' },
        { text: 'AI Analysis', icon: <Scan size={20} />, path: '/demo' },
        { text: 'Alerts', icon: <AlertTriangle size={20} />, path: '/alerts' },
        { text: 'Analytics', icon: <BarChart2 size={20} />, path: '/analytics' },
        { text: 'System', icon: <Settings size={20} />, path: '/system' },
    ];

    const drawerContent = (
        <Box sx={{
            height: '100%',
            background: theme.palette.background.default, // Use theme background
            borderRight: `1px solid ${theme.palette.divider}`,
            backdropFilter: 'blur(10px)'
        }}>
            <Toolbar sx={{ display: 'flex', alignItems: 'center', px: 2, gap: 1.5 }}>
                <Shield color={theme.palette.primary.main} size={28} />
                <Box>
                    <Typography variant="h6" sx={{ color: theme.palette.text.primary, lineHeight: 1, fontWeight: 700 }}>
                        AURORA
                    </Typography>
                    <Typography variant="caption" sx={{ color: theme.palette.text.secondary, letterSpacing: '0.15em', fontWeight: 600 }}>
                        SENTINEL
                    </Typography>
                </Box>
            </Toolbar>
            <List sx={{ mt: 3, px: 2 }}>
                {menuItems.map((item) => (
                    <ListItem
                        button
                        key={item.text}
                        onClick={() => {
                            navigate(item.path);
                            if (isMobile) setMobileOpen(false);
                        }}
                        sx={{
                            mb: 0.5,
                            borderRadius: '12px', // More rounded
                            color: location.pathname === item.path ? theme.palette.primary.contrastText : theme.palette.text.secondary,
                            backgroundColor: location.pathname === item.path ? theme.palette.primary.main : 'transparent',
                            transition: 'all 0.2s ease-in-out',
                            '&:hover': {
                                backgroundColor: location.pathname === item.path ? theme.palette.primary.dark : theme.palette.action.hover,
                                color: location.pathname === item.path ? theme.palette.primary.contrastText : theme.palette.text.primary,
                                transform: 'translateX(3px)',
                                '& .lucide': { color: location.pathname === item.path ? theme.palette.primary.contrastText : theme.palette.primary.main }
                            }
                        }}
                    >
                        <ListItemIcon sx={{ minWidth: 36, color: location.pathname === item.path ? 'inherit' : theme.palette.text.secondary }}>
                            {item.icon}
                        </ListItemIcon>
                        <ListItemText
                            primary={item.text}
                            primaryTypographyProps={{
                                sx: { fontWeight: 600, fontSize: '0.9rem' }
                            }}
                        />
                    </ListItem>
                ))}
            </List>
        </Box>
    );

    return (
        <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
            {/* Top Bar for Mobile */}
            <AppBar
                position="fixed"
                sx={{
                    width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
                    ml: { md: `${DRAWER_WIDTH}px` },
                    display: { md: 'none' },
                    background: theme.palette.background.paper,
                    color: theme.palette.text.primary
                }}
            >
                <Toolbar>
                    <IconButton
                        color="inherit"
                        aria-label="open drawer"
                        edge="start"
                        onClick={handleDrawerToggle}
                        sx={{ mr: 2, display: { md: 'none' } }}
                    >
                        <Menu />
                    </IconButton>
                    <Typography variant="h6" noWrap component="div" fontWeight={700}>
                        AURORA SENTINEL
                    </Typography>
                </Toolbar>
            </AppBar>

            {/* Sidebar Navigation */}
            <Box
                component="nav"
                sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}
            >
                {/* Mobile Drawer */}
                <Drawer
                    variant="temporary"
                    open={mobileOpen}
                    onClose={handleDrawerToggle}
                    ModalProps={{ keepMounted: true }}
                    sx={{
                        display: { xs: 'block', md: 'none' },
                        '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH, border: 'none' },
                    }}
                >
                    {drawerContent}
                </Drawer>

                {/* Desktop Drawer */}
                <Drawer
                    variant="permanent"
                    sx={{
                        display: { xs: 'none', md: 'block' },
                        '& .MuiDrawer-paper': {
                            boxSizing: 'border-box',
                            width: DRAWER_WIDTH,
                            border: 'none',
                            bgcolor: 'transparent'
                        },
                    }}
                    open
                >
                    {drawerContent}
                </Drawer>
            </Box>

            {/* Main Content Area */}
            <Box
                component="main"
                sx={{
                    flexGrow: 1,
                    p: 3,
                    width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
                    mt: { xs: 8, md: 0 },
                    // Clean background without noisy gradients
                    background: theme.palette.background.default,
                }}
            >
                <AnimatePresence mode="wait">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.3 }}
                    >
                        {children}
                    </motion.div>
                </AnimatePresence>
            </Box>
        </Box>
    );
};

export default Layout;
