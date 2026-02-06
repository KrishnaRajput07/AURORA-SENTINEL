import React from 'react';
import { MapContainer, TileLayer, Circle, Popup } from 'react-leaflet';
import { Box, Typography } from '@mui/material';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
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
        if (risk > 75) return '#f43f5e'; // Rose 500 (High Risk)
        if (risk > 50) return '#f97316'; // Orange 500 (Medium Risk)
        if (risk > 25) return '#eab308'; // Yellow 500 (Low Risk)
        return '#14b8a6'; // Teal 500 (Safe)
    };

    return (
        <Box sx={{ height: '100%', width: '100%', borderRadius: 3, overflow: 'hidden', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}>
            <MapContainer
                center={[28.5355, 77.3910]}
                zoom={16}
                style={{ height: '100%', width: '100%' }}
            >
                {/* Clean Light Tiles for Premium Feel */}
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                />

                {cameraLocations.map((camera) => {
                    const risk = getCameraRisk(camera.id);
                    return (
                        <Circle
                            key={camera.id}
                            center={[camera.lat, camera.lng]}
                            radius={40}
                            pathOptions={{
                                fillColor: getRiskColor(risk),
                                fillOpacity: 0.6, // Slightly higher opacity for visibility on light map
                                color: getRiskColor(risk),
                                weight: 2,
                            }}
                        >
                            <Popup className="custom-popup">
                                <Box sx={{ textAlign: 'center' }}>
                                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: '#0f172a' }}>
                                        {camera.name}
                                    </Typography>
                                    <Typography variant="caption" sx={{ color: '#64748b' }}>
                                        ID: {camera.id}
                                    </Typography>
                                    <Typography variant="body2" sx={{ fontWeight: 'bold', color: getRiskColor(risk), mt: 0.5 }}>
                                        Risk Score: {risk.toFixed(1)}
                                    </Typography>
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
