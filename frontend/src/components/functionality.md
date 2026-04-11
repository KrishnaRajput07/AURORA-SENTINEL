# Components — Functionality

This directory contains all React UI components for the AURORA Sentinel frontend.

## Components

### `Layout.jsx`
- Main application shell — AppBar, sidebar navigation, notification center, profile menu
- Role-based navigation: admin sees Admin Panel, operators see standard menu
- Integrates Lucide icons and Framer Motion animations
- Notification popover with deduplication

### `LiveFeed.jsx`
- Real-time surveillance feed via WebSocket (`/ws/live-feed` or `/vlm/intelligent-feed`)
- Renders ML detection overlays (skeletons, bounding boxes, weapon markers) on canvas
- Supports camera device selection and VLM mode toggle
- Performance mode: reduces render frequency for lower-end hardware
- Exports `threatEventEmitter` for cross-component threat alerts

### `AlertQueue.jsx`
- Alert management table with status tabs (Active / Acknowledged / Resolved)
- Acknowledge and resolve actions with dialog forms
- Resolution types: Threat Neutralized, False Positive, Escalated to Police, etc.
- Animated transitions with Framer Motion

### `IntelligencePanel.jsx`
- Side panel for the Intelligence page
- Semantic search, latest events feed, and VLM-powered visual Q&A chat
- Severity filtering, video preview modal, and chat history
- Integrates with `/intelligence/search` and `/intelligence/chat` APIs

### `SurveillanceChatbot.jsx`
- AI chatbot for natural language surveillance queries
- Forced routing: time-range queries → search, counting queries → count
- Renders structured result cards (alerts, clips, events)
- Collapsible interface with chat history

### `RiskHeatmap.jsx`
- Leaflet-based geographic risk heatmap
- Displays alert locations as colored circles (red/orange/yellow by severity)
- Re-center control and marker popups with alert details

### `AnalyticsDashboard.jsx`
- Dashboard analytics widget with stat cards and bar chart
- Displays: total alerts, critical alerts, alert level distribution
- Uses Recharts for visualization

### `ArchiveGallery.jsx`
- Video archive browser with Active / Bin / Processed tabs
- Thumbnail grid with play, download, delete, and restore actions
- Date formatting and safe API date parsing

### `SmartBinSettings.jsx`
- Settings panel for Smart Bin clip capture configuration
- Debounced API updates (1.5s delay) for clip duration and retention days
- Toggle switches for enable/disable with loading states

### `LayoutGrid.jsx`
- Animated grid layout with expand-on-click behavior
- Used on the Dashboard for arranging widget cards

### `NetworkStatusIndicator.jsx`
- Global online/offline status indicator
- Shows a slide-up banner when network connectivity changes
- Auto-hides after 5 seconds when back online

### `__tests__/`
- Component test files (see `__tests__/functionality.md`)

### `ui/`
- Reusable UI utility components (see `ui/functionality.md`)
