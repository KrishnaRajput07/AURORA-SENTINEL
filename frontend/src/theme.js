import { createTheme, alpha } from '@mui/material/styles';

// Aurora Sentinel Premium Theme Configuration
const theme = createTheme({
    palette: {
        mode: 'dark',
        primary: {
            main: '#6366f1', // Indigo 500 - Professional & Trustworthy
            light: '#818cf8',
            dark: '#4338ca',
            contrastText: '#ffffff',
        },
        secondary: {
            main: '#14b8a6', // Teal 500 - Soothing & Fresh
            light: '#2dd4bf',
            dark: '#0d9488',
            contrastText: '#ffffff',
        },
        background: {
            default: '#0f172a', // Slate 900 - Deep, rich blue-grey
            paper: '#1e293b',   // Slate 800 - Slightly lighter
        },
        error: {
            main: '#ef4444', // Red 500
        },
        warning: {
            main: '#f59e0b', // Amber 500
        },
        info: {
            main: '#3b82f6', // Blue 500
        },
        success: {
            main: '#10b981', // Emerald 500
        },
        text: {
            primary: '#f8fafc', // Slate 50
            secondary: '#94a3b8', // Slate 400
        },
        action: {
            hover: alpha('#6366f1', 0.08),
            selected: alpha('#6366f1', 0.16),
        },
    },
    typography: {
        fontFamily: '"Plus Jakarta Sans", "Inter", "Roboto", sans-serif',
        h1: { fontWeight: 700, letterSpacing: '-0.025em', color: '#f8fafc' },
        h2: { fontWeight: 700, letterSpacing: '-0.025em', color: '#f8fafc' },
        h3: { fontWeight: 600, letterSpacing: '-0.025em', color: '#f8fafc' },
        h4: { fontWeight: 600, letterSpacing: '-0.01em' },
        h5: { fontWeight: 600, letterSpacing: '0em' },
        h6: { fontWeight: 600, letterSpacing: '0em' },
        subtitle1: { letterSpacing: '0em', color: '#aecbe6' }, // Softer subtitle
        body1: { fontSize: '1rem', letterSpacing: '0em', lineHeight: 1.6 },
    },
    shape: {
        borderRadius: 16, // More rounded, modern look
    },
    components: {
        MuiCssBaseline: {
            styleOverrides: {
                body: {
                    scrollbarColor: "#334155 #0f172a",
                    "&::-webkit-scrollbar, & *::-webkit-scrollbar": {
                        backgroundColor: "#0f172a",
                        width: 8,
                    },
                    "&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb": {
                        borderRadius: 8,
                        backgroundColor: "#334155", // Slate 700
                        minHeight: 24,
                    },
                    "&::-webkit-scrollbar-thumb:focus, & *::-webkit-scrollbar-thumb:focus": {
                        backgroundColor: "#475569", // Slate 600
                    },
                },
            },
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    backgroundImage: 'none',
                    backgroundColor: alpha('#1e293b', 0.7), // Slate 800 with transparency
                    backdropFilter: 'blur(20px)',
                    border: '1px solid rgba(148, 163, 184, 0.1)', // Subtle Slate border
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)', // Soft shadow
                    transition: 'box-shadow 0.3s ease-in-out, border-color 0.3s ease-in-out',
                    '&:hover': {
                        borderColor: 'rgba(99, 102, 241, 0.2)', // Hint of Indigo on hover
                        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
                    },
                },
            },
        },
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: 12,
                    textTransform: 'none',
                    fontWeight: 600,
                    letterSpacing: '0.01em',
                    padding: '8px 16px',
                },
                containedPrimary: {
                    background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)', // Smooth Indigo Gradient
                    boxShadow: '0 4px 6px -1px rgba(99, 102, 241, 0.3)',
                    '&:hover': {
                        background: 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)',
                        boxShadow: '0 10px 15px -3px rgba(99, 102, 241, 0.4)',
                    },
                },
                containedSecondary: {
                    background: 'linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)', // Smooth Teal Gradient
                    boxShadow: '0 4px 6px -1px rgba(20, 184, 166, 0.3)',
                    '&:hover': {
                        background: 'linear-gradient(135deg, #0d9488 0%, #0f766e 100%)',
                    },
                },
            },
        },
        MuiAppBar: {
            styleOverrides: {
                root: {
                    backgroundColor: alpha('#0f172a', 0.8),
                    backdropFilter: 'blur(16px)',
                    borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                    boxShadow: 'none',
                },
            },
        },
        MuiChip: {
            styleOverrides: {
                root: {
                    fontWeight: 500,
                },
            },
        },
    },
});

export default theme;
