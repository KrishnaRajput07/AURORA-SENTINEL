import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { BrowserRouter } from 'react-router-dom';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        {/* Future flags enabled to suppress v7 warnings */}
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <App />
        </BrowserRouter>
    </React.StrictMode>
);


// Force Unregister any existing Service Workers and Clear Caches
// This solves layout inconsistencies caused by stale persistent service workers.
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then((registrations) => {
        for (let registration of registrations) {
            registration.unregister();
            console.log('Force unmasked old Service Worker:', registration);
        }
    });
}

if ('caches' in window) {
    caches.keys().then((names) => {
        for (let name of names) {
            caches.delete(name);
            console.log('Cleared stale cache:', name);
        }
    });
}
