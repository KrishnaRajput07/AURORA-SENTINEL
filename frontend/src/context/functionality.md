# Context — Functionality

This directory contains React context providers for global state management across the application.

## Context Providers

### `AuthContext.jsx`
- Authentication and user management context
- Stores: current user, operators list, loading state
- Functions: login, logout, updateProfile, addOperator, deleteOperator, verifyOperator
- Persists user and operators to localStorage for session continuity
- Role-based access: admin vs operator

### `IntelligenceContext.jsx`
- Intelligence page state management
- Stores: uploaded file, upload progress, analysis result, drawer state, seek seconds
- Provides centralized state for the video upload and analysis flow
- Enables seeking to specific timestamps from search results

### `NotificationContext.jsx`
- Global notification system with toast and notification center
- Functions: showToast, addNotification, removeNotification, clearNotifications
- Auto-toasts for Critical/Warning level notifications
- Duplication prevention (1-minute window for same title)
- Maintains last 50 notifications
- Material-UI Snackbar with Alert component for visual feedback

### `SettingsContext.jsx`
- Performance mode settings context
- Stores: performanceMode (boolean)
- Persists to localStorage
- Toggles reduced rendering frequency for lower-end hardware
