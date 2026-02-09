import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import ArchiveGallery from '../components/ArchiveGallery';

const Archives = () => {
    return (
        <Box>
            <Typography variant="h5" color="text.primary" sx={{ mb: 3, letterSpacing: '0.05em', fontWeight: 700 }}>
                SECURITY ARCHIVES
            </Typography>
            <Paper sx={{ p: 0, overflow: 'hidden', borderRadius: 4, border: '1px solid rgba(0,0,0,0.05)' }}>
                <ArchiveGallery />
            </Paper>
        </Box>
    );
};

export default Archives;
