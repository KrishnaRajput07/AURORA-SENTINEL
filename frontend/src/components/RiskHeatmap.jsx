import React from 'react';
import { MapContainer, TileLayer, Circle, Popup, Marker } from 'react-leaflet';
import { Box, Typography, useTheme, alpha } from '@mui/material';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix Leaflet icons
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

const RiskHeatmap = ({ alerts }) => {
    const theme = useTheme();

    // Mock camera locations 
    const cameraLocations = [
        { id: 'CAM-001', lat: 28.5355, lng: 77.3910, name: 'Main Gate' },
        { id: 'CAM-002', lat: 28.5365, lng: 77.3920, name: 'Building A' },
        { id: 'CAM-003', lat: 28.5345, lng: 77.3900, name: 'Parking Lot' },
        { id: 'CAM-004', lat: 28.5375, lng: 77.3930, name: 'Sports Complex' },
    ];

    const getCameraRisk = (cameraId) => {
        const recentAlerts = alerts
            .filter(a => a.camera_id === cameraId)
            .slice(0, 10);

        if (recentAlerts.length === 0) return 0;
        return recentAlerts.reduce((sum, a) => sum + a.risk_score, 0) / recentAlerts.length;
    };

    const getRiskColor = (risk) => {
        if (risk > 75) return theme.palette.error.main;
        if (risk > 50) return theme.palette.warning.main;
        if (risk > 25) return theme.palette.info.main;
        return theme.palette.success.main;
    };

    return (
        <Box sx={{ height: '100%', width: '100%', bgcolor: '#E8E2D8' }}>
            <MapContainer
                center={[28.5355, 77.3910]}
                zoom={16}
                style={{ height: '100%', width: '100%' }}
                zoomControl={false}
            >
                {/* Light Mode Tiles - CartoDB Positron for Clean Look */}
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                />

                {cameraLocations.map((camera) => {
                    const risk = getCameraRisk(camera.id);
                    const color = getRiskColor(risk);

                    return (
                        <Circle
                            key={camera.id}
                            center={[camera.lat, camera.lng]}
                            radius={40}
                            pathOptions={{
                                fillColor: color,
                                fillOpacity: 0.4, // Softer opacity
                                color: color,
                                weight: 2,
                            }}
                        >
                            <Popup
                                className="clean-popup"
                                closeButton={false}
                            >
                                <Box sx={{ textAlign: 'center', p: 0.5 }}>
                                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: theme.palette.text.primary }}>
                                        {camera.name}
                                    </Typography>
                                    <Typography variant="caption" sx={{ color: theme.palette.text.secondary, display: 'block' }}>
                                        ID: {camera.id}
                                    </Typography>
                                    <Box sx={{ mt: 1, borderTop: `1px solid ${theme.palette.divider}`, pt: 0.5 }}>
                                        <Typography variant="caption" sx={{ fontWeight: 'bold', color: color }}>
                                            RISK: {risk.toFixed(1)}%
                                        </Typography>
                                    </Box>
                                </Box>
                            </Popup>
                        </Circle>
                    );
                })}
            </MapContainer>
        </Box>
    );
};

export default RiskHeatmap;
