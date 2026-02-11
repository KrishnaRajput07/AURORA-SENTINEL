import React, { createContext, useContext, useState, useCallback } from 'react';

const NotificationContext = createContext(null);

export const NotificationProvider = ({ children }) => {
    const [notifications, setNotifications] = useState([
        { id: 1, title: 'Loitering Detected', time: new Date(), level: 'Warning' },
        { id: 2, title: 'Unauthorized Entry', time: new Date(Date.now() - 1000 * 60 * 5), level: 'Critical' },
        { id: 3, title: 'Camera 04 Offline', time: new Date(Date.now() - 1000 * 60 * 15), level: 'Info' }
    ]);

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
            return [newNotif, ...prev].slice(0, 50); // Keep last 50
        });
    }, []);

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
            removeNotification
        }}>
            {children}
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
