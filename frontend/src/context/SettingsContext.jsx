import React, { createContext, useContext, useState, useEffect } from 'react';

const SettingsContext = createContext();

export const SettingsProvider = ({ children }) => {
    const [performanceMode, setPerformanceMode] = useState(() => {
        const saved = localStorage.getItem('sentinel_performance_mode');
        return saved === 'true';
    });

    useEffect(() => {
        localStorage.setItem('sentinel_performance_mode', performanceMode);
    }, [performanceMode]);

    const togglePerformanceMode = () => setPerformanceMode(prev => !prev);

    return (
        <SettingsContext.Provider value={{ performanceMode, setPerformanceMode, togglePerformanceMode }}>
            {children}
        </SettingsContext.Provider>
    );
};

export const useSettings = () => {
    const context = useContext(SettingsContext);
    if (!context) {
        throw new Error('useSettings must be used within a SettingsProvider');
    }
    return context;
};
