import React from 'react';
import { Grid, Typography, Box, Paper, InputLabel, MenuItem, FormControl, Select } from '@mui/material';
import LiveFeed from '../components/LiveFeed';
import { motion } from 'framer-motion';

const LiveSurveillance = () => {
    // Mock cameras
    const cameras = [
        { id: 'CAM-01', location: 'Main Entrance' },
        { id: 'CAM-02', location: 'Lobby North' },
        { id: 'CAM-03', location: 'Parking Lot A' },
        { id: 'CAM-04', location: 'Server Room' },
    ];

    return (
        <Box>
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h5" color="text.primary" sx={{ letterSpacing: '0.05em' }}>
                    LIVE SURVEILLANCE GRID
                </Typography>
                <FormControl variant="outlined" size="small" sx={{ minWidth: 200, bgcolor: 'rgba(0,0,0,0.3)' }}>
                    <InputLabel id="district-select-label">Select District</InputLabel>
                    <Select
                        labelId="district-select-label"
                        id="district-select"
                        value={10}
                        label="Select District"
                    >
                        <MenuItem value={10}>Sector 7 (Main)</MenuItem>
                        <MenuItem value={20}>Sector 4 (Perimeter)</MenuItem>
                        <MenuItem value={30}>Sector 9 (Restricted)</MenuItem>
                    </Select>
                </FormControl>
            </Box>

            <Grid container spacing={3}>
                {cameras.map((cam, index) => (
                    <Grid item xs={12} md={6} key={cam.id}>
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: index * 0.1 }}
                        >
                            <Paper sx={{
                                p: 0,
                                height: 400,
                                overflow: 'hidden',
                                position: 'relative',
                                '&:hover .camera-label': { opacity: 1 }
                            }}>
                                <LiveFeed />
                                <Box className="camera-label" sx={{
                                    position: 'absolute',
                                    top: 15,
                                    left: 15,
                                    bgcolor: 'rgba(0,0,0,0.7)',
                                    px: 2,
                                    py: 0.5,
                                    borderRadius: 1,
                                    border: '1px solid rgba(0, 243, 255, 0.3)',
                                    pointerEvents: 'none',
                                    transition: 'opacity 0.2s',
                                    opacity: 0.7
                                }}>
                                    <Typography variant="subtitle2" color="primary">{cam.id}</Typography>
                                    <Typography variant="caption" color="text.secondary">{cam.location}</Typography>
                                </Box>
                            </Paper>
                        </motion.div>
                    </Grid>
                ))}
            </Grid>
        </Box>
    );
};

export default LiveSurveillance;
