import React, { createContext, useContext, useState, useCallback } from 'react';
import { Snackbar, Alert } from '@mui/material';

const NotificationContext = createContext(null);

export const NotificationProvider = ({ children }) => {
    const [notifications, setNotifications] = useState([]);
    const [toast, setToast] = useState({ open: false, message: '', severity: 'info' });

    const showToast = useCallback((message, severity = 'info') => {
        setToast({ open: true, message, severity });
    }, []);

    const handleCloseToast = (event, reason) => {
        if (reason === 'clickaway') return;
        setToast(prev => ({ ...prev, open: false }));
    };

    const addNotification = useCallback((notification) => {
        setNotifications(prev => {
            // Check if a similar notification already exists in the last minute to avoid spam
            const isDuplicate = prev.some(n =>
                n.title === notification.title &&
                (new Date() - new Date(n.time)) < 60000
            );
            if (isDuplicate) return prev;

            const newNotif = {
                id: Date.now(),
                time: new Date(),
                ...notification
            };
            
            // Automatically show toast for high priority levels
            if (notification.level === 'Critical' || notification.level === 'Warning') {
                showToast(notification.title, notification.level === 'Critical' ? 'error' : 'warning');
            }

            return [newNotif, ...prev].slice(0, 50); // Keep last 50
        });
    }, [showToast]);

    const clearNotifications = useCallback(() => {
        setNotifications([]);
    }, []);

    const removeNotification = useCallback((id) => {
        setNotifications(prev => prev.filter(n => n.id !== id));
    }, []);

    return (
        <NotificationContext.Provider value={{
            notifications,
            addNotification,
            clearNotifications,
            removeNotification,
            showToast
        }}>
            {children}
            <Snackbar
                open={toast.open}
                autoHideDuration={4000}
                onClose={handleCloseToast}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert 
                    onClose={handleCloseToast} 
                    severity={toast.severity} 
                    variant="filled"
                    sx={{ 
                        width: '100%', 
                        borderRadius: 3, 
                        fontWeight: 700,
                        boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
                        px: 3
                    }}
                >
                    {toast.message}
                </Alert>
            </Snackbar>
        </NotificationContext.Provider>
    );
};

export const useNotifications = () => {
    const context = useContext(NotificationContext);
    if (!context) {
        throw new Error('useNotifications must be used within a NotificationProvider');
    }
    return context;
};
