import React, { createContext, useState, useContext } from 'react';

const IntelligenceContext = createContext();

export const useIntelligence = () => useContext(IntelligenceContext);

export const IntelligenceProvider = ({ children }) => {
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [drawerOpen, setDrawerOpen] = useState(false);
    const [seekSeconds, setSeekSeconds] = useState(null);

    const value = {
        file, setFile,
        uploading, setUploading,
        progress, setProgress,
        analysisResult, setAnalysisResult,
        drawerOpen, setDrawerOpen,
        seekSeconds, setSeekSeconds
    };

    return (
        <IntelligenceContext.Provider value={value}>
            {children}
        </IntelligenceContext.Provider>
    );
};
