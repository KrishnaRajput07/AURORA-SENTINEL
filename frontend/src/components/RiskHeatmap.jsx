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
        { id: 'CAM-001', lat: 28.5355, lng: 77.3910, name: 'Main Gate Entrance' },
        { id: 'CAM-002', lat: 28.5365, lng: 77.3920, name: 'North Wing Corridor' },
        { id: 'CAM-003', lat: 28.5345, lng: 77.3900, name: 'South Parking Zone' },
        { id: 'CAM-004', lat: 28.5375, lng: 77.3930, name: 'Loading Dock Area' },
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
        <Box sx={{
            height: '100%',
            width: '100%',
            bgcolor: '#F8FAFC',
            position: 'relative',
            '& .leaflet-container': {
                fontFamily: 'inherit',
                background: '#F8FAFC'
            }
        }}>
            <MapContainer
                center={[28.5355, 77.3910]}
                zoom={16}
                style={{ height: '100%', width: '100%' }}
                zoomControl={false}
            >
                {/* Clean, high-contrast light tiles */}
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                />

                {cameraLocations.map((camera) => {
                    const risk = getCameraRisk(camera.id);
                    const color = getRiskColor(risk);

                    return (
                        <React.Fragment key={camera.id}>
                            {/* Pulsing Outer Ring for High Risk */}
                            {risk > 50 && (
                                <Circle
                                    center={[camera.lat, camera.lng]}
                                    radius={60}
                                    pathOptions={{
                                        fillColor: color,
                                        fillOpacity: 0.1,
                                        color: color,
                                        weight: 1,
                                        className: 'pulse-circle'
                                    }}
                                />
                            )}

                            <Circle
                                center={[camera.lat, camera.lng]}
                                radius={risk > 75 ? 45 : 35}
                                pathOptions={{
                                    fillColor: color,
                                    fillOpacity: 0.5,
                                    color: color,
                                    weight: 2,
                                }}
                            >
                                <Popup closeButton={false} offset={[0, -10]}>
                                    <Box sx={{
                                        minWidth: 160,
                                        p: 1.5,
                                        borderRadius: 2,
                                        textAlign: 'center'
                                    }}>
                                        <Typography variant="overline" sx={{
                                            fontWeight: 900,
                                            color: theme.palette.text.secondary,
                                            letterSpacing: '0.1em',
                                            lineHeight: 1,
                                            display: 'block',
                                            mb: 1
                                        }}>
                                            ZONE MONITOR
                                        </Typography>
                                        <Typography variant="subtitle1" sx={{ fontWeight: 800, color: theme.palette.text.primary, lineHeight: 1.2 }}>
                                            {camera.name}
                                        </Typography>

                                        <Box sx={{
                                            mt: 2,
                                            pt: 1.5,
                                            borderTop: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            gap: 1
                                        }}>
                                            <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: color, boxShadow: `0 0 8px ${color}` }} />
                                            <Typography variant="h6" sx={{ fontWeight: 900, color: color, fontSize: '1rem', fontFamily: 'monospace' }}>
                                                {risk.toFixed(0)}% RISK
                                            </Typography>
                                        </Box>
                                    </Box>
                                </Popup>
                            </Circle>
                        </React.Fragment>
                    );
                })}
            </MapContainer>

            {/* Injected Pulsing CSS */}
            <style>
                {`
                .pulse-circle {
                    animation: leaflet-pulse 2s infinite ease-out;
                }
                @keyframes leaflet-pulse {
                    0% { stroke-width: 1; stroke-opacity: 0.8; fill-opacity: 0.2; }
                    100% { stroke-width: 15; stroke-opacity: 0; fill-opacity: 0; }
                }
                .leaflet-popup-content-wrapper {
                    background: rgba(255, 255, 255, 0.9) !important;
                    backdrop-filter: blur(12px) !important;
                    border-radius: 16px !important;
                    box-shadow: 0 12px 32px rgba(0,0,0,0.15) !important;
                    border: 1px solid rgba(255,255,255,0.3) !important;
                    overflow: hidden !important;
                }
                .leaflet-popup-tip {
                    background: rgba(255, 255, 255, 0.9) !important;
                    backdrop-filter: blur(12px) !important;
                }
                .leaflet-popup-content {
                    margin: 0 !important;
                    width: auto !important;
                }
                `}
            </style>
        </Box>
    );
};

export default RiskHeatmap;
