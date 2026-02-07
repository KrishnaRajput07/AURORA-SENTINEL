import { createTheme } from '@mui/material/styles';

// Palette:
// #BFC6C4 - Silver/Gray (Neutral, Borders, Secondary Text)
// #E8E2D8 - Beige/Almond (Background, Warmth)
// #6F8F72 - Sage Green (Primary, Success, Active)
// #F2A65A - Sandy Brown/Terracotta (Secondary, Highlights, Warnings)

const theme = createTheme({
    palette: {
        mode: 'light',
        primary: {
            main: '#6F8F72', // Sage Green
            light: '#8FA991',
            dark: '#516B54',
            contrastText: '#FFFFFF',
        },
        secondary: {
            main: '#F2A65A', // Terracotta
            light: '#F5B87D',
            dark: '#C48240',
            contrastText: '#FFFFFF',
        },
        background: {
            default: '#E8E2D8', // Beige Background
            paper: '#FFFFFF',   // Clean White Paper for contrast
        },
        text: {
            primary: '#2C3333', // Deep Black/Green for Readability
            secondary: '#6D7474', // Muted Gray/Green
        },
        action: {
            active: '#6F8F72',
            hover: 'rgba(111, 143, 114, 0.08)',
            selected: 'rgba(111, 143, 114, 0.16)',
        },
        divider: '#BFC6C4', // Silver Gray for borders
        error: {
            main: '#D9534F', // Standard red for critical errors
        },
        success: {
            main: '#6F8F72',
        },
        warning: {
            main: '#F2A65A',
        },
        info: {
            main: '#BFC6C4',
        },
    },
    typography: {
        fontFamily: '"Inter", sans-serif',
        h1: { fontWeight: 700, color: '#2C3333', letterSpacing: '-0.02em' },
        h2: { fontWeight: 700, color: '#2C3333', letterSpacing: '-0.01em' },
        h3: { fontWeight: 700, color: '#2C3333' },
        h4: { fontWeight: 600, color: '#2C3333' },
        h5: { fontWeight: 600, color: '#2C3333', letterSpacing: '0.02em' },
        h6: { fontWeight: 600, color: '#2C3333' },
        subtitle1: { fontWeight: 500, color: '#4A5568' },
        subtitle2: { fontWeight: 600, color: '#6F8F72', textTransform: 'uppercase', letterSpacing: '0.05em' },
        body1: { color: '#2C3333', lineHeight: 1.6 },
        body2: { color: '#6D7474', lineHeight: 1.6 },
        button: { fontWeight: 600, textTransform: 'none' },
    },
    shape: {
        borderRadius: 12, // Increased for a softer, slightly rounded look
    },
    components: {
        MuiCssBaseline: {
            styleOverrides: {
                body: {
                    backgroundColor: '#E8E2D8',
                },
            },
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    border: '1px solid #BFC6C4',
                    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
                    overflow: 'hidden', // Ensures content respects the border radius
                    '&:hover': {
                        borderColor: '#6F8F72', // Active border on hover
                        boxShadow: '0 4px 12px rgba(111, 143, 114, 0.15)',
                    },
                },
                elevation0: {
                    boxShadow: 'none',
                    border: '1px solid #BFC6C4',
                }
            },
        },
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: 8, // Buttons slightly sharper than containers
                    padding: '8px 22px',
                    boxShadow: 'none',
                    '&:hover': {
                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                    },
                },
                containedPrimary: {
                    backgroundColor: '#6F8F72',
                    '&:hover': {
                        backgroundColor: '#5A755D',
                    },
                },
            },
        },
        MuiAppBar: {
            styleOverrides: {
                root: {
                    backgroundColor: '#FFFFFF',
                    borderBottom: '1px solid #BFC6C4',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
                    color: '#2C3333',
                },
            },
        },
        MuiTab: {
            styleOverrides: {
                root: {
                    textTransform: 'none',
                    fontWeight: 600,
                    color: '#6D7474',
                    '&.Mui-selected': {
                        color: '#6F8F72',
                    },
                },
            },
        },
        MuiChip: {
            styleOverrides: {
                root: {
                    fontWeight: 600,
                    borderRadius: 8,
                },
            },
        },
    },
});

export default theme;
