import React, { useState, useEffect } from 'react';
import { Search, Brain, Play, Clock, AlertTriangle, Activity } from 'lucide-react';

const IntelligencePanel = () => {
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
            const res = await fetch('http://localhost:8000/intelligence/latest');
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
            const res = await fetch(`http://localhost:8000/intelligence/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            setResults(data);
        } catch (e) {
            console.error("Search failed:", e);
        } finally {
            setIsSearching(false);
        }
    };

    const triggerProcessing = async () => {
        await fetch('http://localhost:8000/intelligence/process', { method: 'POST' });
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
                            src={`http://localhost:8000/recordings/${video.filename}`}
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

    return (
        <div className="bg-gray-900 border-l border-cyan-900/30 h-full flex flex-col w-96">
            {/* Header */}
            <div className="p-4 border-b border-cyan-900/30">
                <div className="flex items-center gap-2 mb-4">
                    <Brain className="w-6 h-6 text-purple-400" />
                    <h2 className="text-lg font-bold text-white tracking-wider">CORTEX ARCHIVE</h2>
                </div>

                {/* Search Bar */}
                <form onSubmit={handleSearch} className="relative">
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

                <div className="flex gap-2 mt-4 text-xs font-mono">
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

                {activeTab === 'search' && !isSearching && results.length === 0 && (
                    <div className="text-center text-gray-600 mt-10 text-sm">No semantic matches found.</div>
                )}

                {(activeTab === 'latest' ? latestEvents : results).map((item, idx) => {
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

                    return (
                        <div
                            key={idx}
                            onClick={() => setSelectedVideo(item)}
                            className={`group border ${borderColor} rounded-lg p-3 cursor-pointer transition-all mb-2 relative overflow-hidden 
                                ${isAudioEvent ? 'bg-indigo-900/20 border-indigo-500/30 hover:bg-indigo-900/40' : 'bg-black/40 hover:bg-gray-900 hover:border-cyan-500/50'}
                            `}
                        >
                            {/* Audio Waveform Decoration */}
                            {isAudioEvent && (
                                <div className="absolute -right-4 -top-4 opacity-10 text-indigo-500 transform rotate-12">
                                    <Activity size={64} />
                                </div>
                            )}

                            <div className="flex justify-between items-start mb-2 relative z-10">
                                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border 
                                    ${isAudioEvent ? 'text-indigo-300 bg-indigo-900/50 border-indigo-700' : 'text-cyan-500/80 bg-cyan-950/30 border-cyan-900/50'}`}>
                                    {isAudioEvent ? 'AUDIO DETECTED' : item.filename.split('-').pop()}
                                </span>
                                <span className="text-[10px] font-mono text-gray-500 bg-black/50 px-2 py-0.5 rounded">
                                    {typeof item.timestamp === 'number' ? item.timestamp.toFixed(1) : item.timestamp}s
                                </span>
                            </div>

                            <div className="flex items-start gap-2 relative z-10">
                                {isAudioEvent && (
                                    <div className="mt-0.5 min-w-[20px]">
                                        {isGunshot && <span className="text-lg">🔫</span>}
                                        {isScream && <span className="text-lg">🗣️</span>}
                                        {isGlass && <span className="text-lg">🪟</span>}
                                        {!isGunshot && !isScream && !isGlass && <span className="text-lg">🔊</span>}
                                    </div>
                                )}
                                <p className={`text-xs line-clamp-2 leading-relaxed opacity-90 transition-opacity ${isAudioEvent ? 'text-indigo-200 group-hover:text-white' : 'text-gray-300 group-hover:text-white'}`}>
                                    {item.description}
                                </p>
                            </div>

                            {item.score !== undefined && (
                                <div className="mt-3 flex items-center justify-between border-t border-gray-800 pt-2">
                                    <div className="flex items-center gap-2">
                                        <div className={`w-1.5 h-1.5 rounded-full ${scoreDisplay > 60 ? 'bg-red-500 animate-pulse' : 'bg-gray-600'}`}></div>
                                        <span className="text-[10px] uppercase font-bold text-gray-500 tracking-wider">Confidence</span>
                                    </div>
                                    <span className={`text-base font-bold font-mono ${confidenceColor}`}>
                                        {scoreDisplay}%
                                    </span>
                                </div>
                            )}

                            {/* Threat Tags (Video & Audio) */}
                            <div className="flex gap-1 mt-2 flex-wrap">
                                {['gun', 'knife', 'weapon', 'fight', 'punch', 'altercation', 'blood', 'scream', 'glass', 'explosion'].map(keyword => {
                                    if (item.description.toLowerCase().includes(keyword)) {
                                        return (
                                            <span key={keyword} className="text-[9px] px-1.5 py-0.5 bg-red-500/20 text-red-200 border border-red-500/30 rounded uppercase font-bold tracking-wider">
                                                {keyword}
                                            </span>
                                        )
                                    }
                                    return null;
                                })}
                            </div>
                        </div>
                    );
                })}
            </div>

            <VideoModal video={selectedVideo} onClose={() => setSelectedVideo(null)} />
        </div>
    );
};

export default IntelligencePanel;
