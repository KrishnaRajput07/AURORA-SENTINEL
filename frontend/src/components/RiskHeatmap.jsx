import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Circle, Popup, Marker, useMap } from 'react-leaflet';
import { Box, Typography, useTheme, alpha, IconButton } from '@mui/material';
import { Maximize2, Navigation } from 'lucide-react';
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

const ReCenter = ({ center }) => {
    const map = useMap();
    useEffect(() => {
        if (center) {
            map.setView(center, map.getZoom());
        }
    }, [center, map]);
    return null;
};

const RiskHeatmap = ({ alerts }) => {
    const theme = useTheme();
    const [mapCenter, setMapCenter] = useState([28.5355, 77.3910]); // Default Noida
    const [systemLocation, setSystemLocation] = useState(null);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const mapRef = useRef(null);

    useEffect(() => {
        if ("geolocation" in navigator) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const { latitude, longitude } = position.coords;
                    const newCenter = [latitude, longitude];
                    setMapCenter(newCenter);
                    setSystemLocation(newCenter);
                    console.log("System location detected:", newCenter);
                },
                (error) => {
                    console.error("Error getting system location:", error);
                },
                { enableHighAccuracy: true }
            );
        }
    }, []);

    // Mock camera locations 
    const cameraLocations = [
        { id: 'CAM-001', lat: 28.5355, lng: 77.3910, name: 'Main Gate Entrance' },
        { id: 'CAM-002', lat: 28.5365, lng: 77.3920, name: 'North Wing Corridor' },
        { id: 'CAM-003', lat: 28.5345, lng: 77.3900, name: 'South Parking Zone' },
        { id: 'CAM-004', lat: 28.5375, lng: 77.3930, name: 'Loading Dock Area' },
        { id: 'FORENSIC-01', lat: 28.5350, lng: 77.3935, name: 'Forensic Lab Unit' },
    ];

    const getCameraRisk = (cameraId) => {
        const recentAlerts = (alerts || [])
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

    const toggleFullscreen = () => {
        if (!mapRef.current) return;
        
        if (!isFullscreen) {
            mapRef.current._container.requestFullscreen();
            setIsFullscreen(true);
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
            setIsFullscreen(false);
        }
    };

    const handleZoomIn = () => {
        if (mapRef.current) {
            mapRef.current.zoomIn();
        }
    };

    const handleZoomOut = () => {
        if (mapRef.current) {
            mapRef.current.zoomOut();
        }
    };

    return (
        <Box sx={{
            height: '100%',
            width: '100%',
            bgcolor: '#F8FAFC',
            position: 'relative',
            '&:fullscreen': {
                '& .map-controls': {
                    bottom: 20,
                    right: 20
                }
            }
        }}>
            <MapContainer
                center={mapCenter}
                zoom={16}
                style={{ height: '100%', width: '100%' }}
                zoomControl={false}
                ref={mapRef}
            >
                <ReCenter center={mapCenter} />
                
                {/* Clean, high-contrast light tiles */}
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                />

                {systemLocation && (
                    <Marker position={systemLocation}>
                        <Popup>
                            <Typography sx={{ fontWeight: 700 }}>My System Location</Typography>
                        </Popup>
                    </Marker>
                )}

                {cameraLocations.map((camera) => {
                    const risk = getCameraRisk(camera.id);
                    const color = getRiskColor(risk);

                    return (
                        <React.Fragment key={camera.id}>
                            {/* Pulsing Outer Ring for High Risk */}
                            {risk > 50 && (
                                <Circle
                                    center={[camera.lat, camera.lng]}
                                    radius={isFullscreen ? 80 : 60}
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
                                radius={isFullscreen ? risk > 75 ? 60 : 45 : isFullscreen ? 35 : 25}
                                pathOptions={{
                                    fillColor: color,
                                    fillOpacity: 0.6,
                                    color: color,
                                    weight: 2,
                                }}
                            >
                                <Popup closeButton={false} offset={[0, -10]}>
                                    <Box sx={{
                                        minWidth: isFullscreen ? 200 : 160,
                                        p: isFullscreen ? 2 : 1.5,
                                        borderRadius: 2,
                                        textAlign: 'center',
                                        bgcolor: 'rgba(255,255,255,0.95)',
                                        backdropFilter: 'blur(12px)',
                                        border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
                                        boxShadow: '0 8px 24px rgba(0,0,0,0.15)'
                                    }}>
                                        <Typography variant="overline" sx={{
                                            fontWeight: 900,
                                            color: theme.palette.text.secondary,
                                            letterSpacing: '0.1em',
                                            lineHeight: 1,
                                            display: 'block',
                                            mb: 0.5,
                                            fontSize: isFullscreen ? '0.8rem' : '0.7rem'
                                        }}>
                                            ZONE MONITOR
                                        </Typography>
                                        <Typography variant="subtitle1" sx={{ 
                                            fontWeight: 800, 
                                            color: theme.palette.text.primary, 
                                            lineHeight: 1.2,
                                            fontSize: isFullscreen ? '1rem' : '0.85rem'
                                        }}>
                                            {camera.name}
                                        </Typography>

                                        <Box sx={{
                                            mt: isFullscreen ? 2 : 1.5,
                                            pt: isFullscreen ? 1.5 : 1,
                                            borderTop: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            gap: 1
                                        }}>
                                            <Box sx={{ 
                                                width: isFullscreen ? 10 : 8, 
                                                height: isFullscreen ? 10 : 8, 
                                                borderRadius: '50%', 
                                                bgcolor: color, 
                                                boxShadow: `0 0 ${isFullscreen ? 12 : 8}px ${color}` 
                                            }} />
                                            <Typography variant="h6" sx={{ 
                                                fontWeight: 900, 
                                                color: color, 
                                                fontSize: isFullscreen ? '1.1rem' : '0.9rem',
                                                fontFamily: 'monospace'
                                            }}>
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

            {/* Enhanced Map Controls */}
            <Box className="map-controls" sx={{
                position: 'absolute',
                bottom: 20,
                right: 20,
                zIndex: 1000,
                display: 'flex',
                flexDirection: 'column',
                gap: 1,
                transition: 'all 0.3s ease'
            }}>
                {/* Zoom Controls */}
                <Box sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 0.5,
                    bgcolor: 'rgba(255,255,255,0.9)',
                    borderRadius: 2,
                    p: 0.5,
                    boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                }}>
                    <IconButton
                        size="small"
                        onClick={handleZoomIn}
                        sx={{
                            color: theme.palette.text.secondary,
                            '&:hover': { color: theme.palette.primary.main, bgcolor: alpha(theme.palette.primary.main, 0.1) }
                        }}
                        title="Zoom In"
                    >
                        <Navigation size={16} />
                    </IconButton>
                    <IconButton
                        size="small"
                        onClick={handleZoomOut}
                        sx={{
                            color: theme.palette.text.secondary,
                            '&:hover': { color: theme.palette.primary.main, bgcolor: alpha(theme.palette.primary.main, 0.1) }
                        }}
                        title="Zoom Out"
                    >
                        <Navigation size={16} style={{ transform: 'rotate(180deg)' }} />
                    </IconButton>
                </Box>

                {/* Fullscreen Toggle */}
                <IconButton
                    size="small"
                    onClick={toggleFullscreen}
                    sx={{
                        bgcolor: isFullscreen ? theme.palette.primary.main : 'rgba(255,255,255,0.9)',
                        color: isFullscreen ? '#fff' : theme.palette.text.secondary,
                        '&:hover': { 
                            bgcolor: isFullscreen ? theme.palette.primary.dark : alpha(theme.palette.primary.main, 0.1),
                            color: '#fff'
                        }
                    }}
                    title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
                >
                    <Maximize2 size={16} />
                </IconButton>
            </Box>

            {/* Injected CSS */}
            <style>{`
                .pulse-circle {
                    animation: leaflet-pulse 2s infinite ease-out;
                }
                @keyframes leaflet-pulse {
                    0% { stroke-width: 1; stroke-opacity: 0.8; fill-opacity: 0.2; }
                    100% { stroke-width: 15; stroke-opacity: 0; fill-opacity: 0; }
                }
                .leaflet-popup-content-wrapper {
                    background: rgba(255, 255, 255, 0.95) !important;
                    backdrop-filter: blur(12px) !important;
                    border-radius: 16px !important;
                    box-shadow: 0 12px 32px rgba(0,0,0,0.15) !important;
                    border: 1px solid rgba(255,255,255,0.3) !important;
                    overflow: hidden !important;
                }
                .leaflet-popup-tip {
                    background: rgba(255, 255, 255, 0.95) !important;
                    backdrop-filter: blur(12px) !important;
                }
                .leaflet-popup-content {
                    margin: 0 !important;
                    width: auto !important;
                }
                .leaflet-container {
                    font-family: inherit !important;
                    background: #F8FAFC !important;
                }
            `}</style>
        </Box>
    );
};

export default RiskHeatmap;
