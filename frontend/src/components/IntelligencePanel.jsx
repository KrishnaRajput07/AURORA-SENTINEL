import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';
import { Search, Brain, Play, Clock, AlertTriangle, Activity } from 'lucide-react';

const IntelligencePanel = () => {
    const [selectedSeverity, setSelectedSeverity] = useState('ALL');
    const [selectedThreat, setSelectedThreat] = useState(null);
    const [activeTab, setActiveTab] = useState('latest'); // 'latest' or 'search'
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [latestEvents, setLatestEvents] = useState([]);
    const [isSearching, setIsSearching] = useState(false);
    const [selectedVideo, setSelectedVideo] = useState(null);

    // Fetch latest insights on mount
    useEffect(() => {
        fetchLatest();
    }, []);

    const fetchLatest = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/intelligence/latest`);
            const data = await res.json();
            setLatestEvents(data);
        } catch (e) {
            console.error("Failed to fetch latest:", e);
        }
    };

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        setIsSearching(true);
        setActiveTab('search');
        try {
            const res = await fetch(`${API_BASE_URL}/intelligence/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            setResults(data);
        } catch (e) {
            console.error("Search failed:", e);
        } finally {
            setIsSearching(false);
        }
    };

    const triggerProcessing = async () => {
        await fetch(`${API_BASE_URL}/intelligence/process`, { method: 'POST' });
        alert("Background processing started! Check terminal for progress.");
    };

    const VideoModal = ({ video, onClose }) => {
        if (!video) return null;
        return (
            <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
                <div className="bg-gray-900 rounded-lg max-w-4xl w-full p-4 border border-cyan-500/30">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-xl font-bold text-cyan-400">Analysis Replay</h3>
                        <button onClick={onClose} className="text-gray-400 hover:text-white">✕</button>
                    </div>
                    <div className="aspect-video bg-black rounded border border-gray-800 mb-4 relative">
                        <video
                            src={`${API_BASE_URL}/recordings/${video.filename}`}
                            controls
                            autoPlay
                            className="w-full h-full object-contain"
                        />
                        <div className="absolute bottom-4 left-4 right-4 bg-black/60 p-2 text-white text-sm rounded">
                            <span className="text-cyan-400 font-bold">{video.timestamp}s:</span> {video.description}
                        </div>
                    </div>
                    <div className="text-xs text-gray-500 font-mono">
                        FILE: {video.filename} | SCORE: {video.score ? video.score.toFixed(3) : 'N/A'}
                    </div>
                </div>
            </div>
        );
    };

    // Filter Logic
    const getFilteredResults = () => {
        const source = activeTab === 'latest' ? latestEvents : results;
        return source.filter(item => {
            // Severity Filter
            if (selectedSeverity !== 'ALL') {
                const itemSev = (item.severity || 'low').toUpperCase();
                if (itemSev !== selectedSeverity) return false;
            }
            // Threat Filter
            if (selectedThreat) {
                const threats = (item.threats || []).map(t => t.toLowerCase());
                const desc = (item.description || '').toLowerCase();
                const term = selectedThreat.toLowerCase();
                // Check structured threats OR description fallback
                if (!threats.includes(term) && !desc.includes(term)) return false;
            }
            return true;
        });
    };

    const filteredResults = getFilteredResults();

    return (
        <div className="bg-gray-900 border-l border-cyan-900/30 h-full flex flex-col w-96">
            {/* Header */}
            <div className="p-4 border-b border-cyan-900/30">
                <div className="flex items-center gap-2 mb-4">
                    <Brain className="w-6 h-6 text-purple-400" />
                    <h2 className="text-lg font-bold text-white tracking-wider">CORTEX VLM SEARCH</h2>
                </div>

                {/* Search Bar */}
                <form onSubmit={handleSearch} className="relative mb-3">
                    <input
                        type="text"
                        placeholder='Search "man with knife"...'
                        className="w-full bg-black/50 border border-gray-700 rounded px-4 py-2 text-sm text-white focus:border-purple-500 focus:outline-none"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                    <button type="submit" className="absolute right-2 top-2 text-gray-400 hover:text-white">
                        <Search className="w-4 h-4" />
                    </button>
                </form>

                {/* FILTERS */}
                <div className="space-y-2 mb-2">
                    {/* Severity Tabs */}
                    <div className="flex bg-black/40 rounded p-1 gap-1">
                        {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map(sev => (
                            <button
                                key={sev}
                                onClick={() => setSelectedSeverity(sev)}
                                className={`flex-1 text-[10px] font-bold py-1 rounded transition-colors ${selectedSeverity === sev
                                    ? 'bg-purple-600/80 text-white'
                                    : 'text-gray-500 hover:text-gray-300'
                                    }`}
                            >
                                {sev}
                            </button>
                        ))}
                    </div>

                    {/* Threat Chips */}
                    <div className="flex flex-wrap gap-1.5">
                        {['GUN', 'KNIFE', 'FIGHT', 'FIRE', 'BLOOD'].map(threat => (
                            <button
                                key={threat}
                                onClick={() => setSelectedThreat(selectedThreat === threat ? null : threat)}
                                className={`text-[9px] px-2 py-0.5 rounded border transition-colors ${selectedThreat === threat
                                    ? 'bg-red-500/20 border-red-500 text-red-200'
                                    : 'bg-transparent border-gray-700 text-gray-500 hover:border-gray-500'
                                    }`}
                            >
                                {threat}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="flex gap-2 mt-2 text-xs font-mono border-t border-gray-800 pt-3">
                    <button
                        onClick={() => setActiveTab('latest')}
                        className={`px-3 py-1 rounded ${activeTab === 'latest' ? 'bg-cyan-900/50 text-cyan-300' : 'text-gray-500 hover:text-gray-300'}`}
                    >
                        LATEST
                    </button>
                    <button
                        onClick={() => setActiveTab('search')}
                        className={`px-3 py-1 rounded ${activeTab === 'search' ? 'bg-purple-900/50 text-purple-300' : 'text-gray-500 hover:text-gray-300'}`}
                    >
                        RESULTS
                    </button>
                    <button onClick={triggerProcessing} className="ml-auto text-green-500 hover:text-green-400">
                        + PROCESS
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {activeTab === 'search' && isSearching && (
                    <div className="text-center text-gray-500 animate-pulse mt-10">Searching Neural Index...</div>
                )}

                {activeTab === 'search' && !isSearching && filteredResults.length === 0 && (
                    <div className="text-center text-gray-600 mt-10 text-sm">No semantic matches found.</div>
                )}

                {activeTab === 'latest' && filteredResults.length === 0 && (
                    <div className="text-center text-gray-600 mt-10 text-sm">No recent events match filters.</div>
                )}

                {filteredResults.map((item, idx) => {
                    // Determine color based on matching score (for search) or severity (for latest)
                    // Search results have 'score' (distance? No, cosine similarity usually. 0-1)
                    // Note: Chroma return distance by default? We need to accept SearchService behavior.
                    // Assuming higher score = better match.

                    let confidenceColor = 'text-gray-500';
                    let borderColor = 'border-gray-800';
                    let scoreDisplay = 0;

                    if (item.score !== undefined) {
                        // Score is now 0-1 normalized from backend
                        scoreDisplay = Math.round(item.score * 100);

                        if (scoreDisplay > 70) {
                            confidenceColor = 'text-red-400';
                            borderColor = 'border-red-900/50';
                        } else if (scoreDisplay > 50) {
                            confidenceColor = 'text-yellow-400';
                            borderColor = 'border-yellow-900/50';
                        }
                    }

                    const isAudioEvent = item.provider === 'audio-ast';
                    const isGunshot = item.description.toLowerCase().includes('gunshot');
                    const isScream = item.description.toLowerCase().includes('scream');
                    const isGlass = item.description.toLowerCase().includes('glass');

                    // Clean JSON artifacts from description if present
                    let cleanDescription = item.description;
                    if (cleanDescription.trim().startsWith('```json')) {
                        cleanDescription = cleanDescription.replace(/```json/g, '').replace(/```/g, '').trim();
                        try {
                            const parsed = JSON.parse(cleanDescription);
                            cleanDescription = parsed.summary || cleanDescription;
                        } catch (e) { /* keep original */ }
                    }
                    if (cleanDescription.trim().startsWith('{')) {
                        try {
                            const parsed = JSON.parse(cleanDescription);
                            cleanDescription = parsed.summary || cleanDescription;
                        } catch (e) { /* keep original */ }
                    }

                    return (
                        <div
                            key={idx}
                            onClick={() => setSelectedVideo(item)}
                            className={`group rounded-lg p-4 cursor-pointer transition-all mb-4 relative overflow-hidden border border-transparent hover:border-cyan-500/30
                                ${isAudioEvent ? 'bg-indigo-900/10' : 'bg-black/40'}
                            `}
                        >
                            {/* Audio Waveform Decoration */}
                            {isAudioEvent && (
                                <div className="absolute -right-4 -top-4 opacity-10 text-indigo-500 transform rotate-12">
                                    <Activity size={80} />
                                </div>
                            )}

                            {/* Header: Filename and Time */}
                            <div className="flex justify-between items-center mb-3 border-b border-gray-800 pb-2">
                                <span className={`text-sm font-bold tracking-wide 
                                    ${isAudioEvent ? 'text-indigo-400' : 'text-cyan-400'}`}>
                                    {isAudioEvent ? 'AUDIO EVENT' : item.filename}
                                </span>
                                <div className="flex items-center gap-2">
                                    <Clock size={12} className="text-gray-600" />
                                    <span className="text-xs font-mono text-gray-500">
                                        {typeof item.timestamp === 'number' ? item.timestamp.toFixed(1) : item.timestamp}s
                                    </span>
                                </div>
                            </div>

                            {/* Main Content: Description */}
                            <div className="mb-3">
                                <div className="flex items-start gap-3">
                                    {isAudioEvent ? (
                                        <div className="mt-1">
                                            {isGunshot && <span className="text-xl">🔫</span>}
                                            {isScream && <span className="text-xl">🗣️</span>}
                                            {isGlass && <span className="text-xl">🪟</span>}
                                            {!isGunshot && !isScream && !isGlass && <span className="text-xl">🔊</span>}
                                        </div>
                                    ) : (
                                        <div className="mt-1 text-gray-600">
                                            <Play size={16} />
                                        </div>
                                    )}

                                    <p className={`text-sm leading-relaxed opacity-90 ${isAudioEvent ? 'text-indigo-100' : 'text-gray-300'}`}>
                                        {cleanDescription}
                                    </p>
                                </div>
                            </div>

                            {/* Footer: Tags and Score */}
                            <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-800/50">
                                {/* Threat Tags */}
                                <div className="flex gap-2 flex-wrap">
                                    {['gun', 'knife', 'weapon', 'fight', 'punch', 'altercation', 'blood', 'scream', 'glass', 'explosion'].map(keyword => {
                                        if (item.description.toLowerCase().includes(keyword)) {
                                            return (
                                                <span key={keyword} className="text-[10px] px-2 py-0.5 bg-red-500/20 text-red-300 border border-red-500/30 rounded uppercase font-bold tracking-wider">
                                                    {keyword}
                                                </span>
                                            )
                                        }
                                        return null;
                                    })}
                                </div>

                                {item.score !== undefined && (
                                    <div className="flex items-center gap-2">
                                        <div className={`w-1.5 h-1.5 rounded-full ${scoreDisplay > 60 ? 'bg-red-500 animate-pulse' : 'bg-gray-600'}`}></div>
                                        <span className={`text-xs font-bold font-mono ${confidenceColor}`}>
                                            {scoreDisplay}% CONTEX
                                        </span>
                                    </div>
                                )}
                            </div>

                            {/* Bottom Divider Line (Visual Separation) */}
                            <div className="w-full h-px bg-gradient-to-r from-transparent via-cyan-900/30 to-transparent mt-4"></div>
                        </div>
                    );
                })}
            </div>

            <VideoModal video={selectedVideo} onClose={() => setSelectedVideo(null)} />
        </div>
    );
};

export default IntelligencePanel;

