# Pages — Functionality

This directory contains the page-level React components — each page corresponds to a major route in the application.

## Pages

### `LandingPage.jsx` + `LandingPage.css`
- Public marketing landing page for AURORA Sentinel
- Animated hero section with canvas background effects
- Features overview, demo video modal, and call-to-action
- Responsive design with mobile menu
- Redirects authenticated users to dashboard

### `Login.jsx`
- Authentication page with role selection (admin vs operator)
- Animated mascot with mouse-following spotlight effect
- Password visibility toggle
- Framer Motion 3D tilt effect on login card
- Validates operator credentials against stored operators list

### `Dashboard.jsx`
- Main dashboard with overview of system status
- LayoutGrid of widget cards: RiskHeatmap, AlertQueue, LiveFeed, AnalyticsDashboard
- Personalized greeting with random international greetings
- Real-time alert notifications integration

### `LiveSurveillance.jsx`
- Full-screen surveillance page
- Expanded LiveFeed component with larger viewing area
- Minimal UI for focused monitoring

### `Intelligence.jsx`
- Video upload and analysis page
- Drag-and-drop file upload with react-dropzone
- Video player with timestamp seeking
- IntelligencePanel sidebar for search and chat
- PDF report generation (jsPDF + autoTable)
- Severity classification and location type selection

### `Alerts.jsx`
- Full-page alert management
- Wrapper around AlertQueue with expanded view

### `Analytics.jsx`
- Detailed analytics page with charts and statistics
- Time-series data visualization
- Alert trend analysis

### `Archives.jsx`
- Video archive browser page
- Wrapper around ArchiveGallery with full-screen layout

### `System.jsx`
- System configuration and health monitoring
- Tabs: Overview, Smart Bin, Settings, Profile
- Health check display (models, GPU, database, AI models)
- Performance mode toggle
- Manual calibration trigger

### `AdminDashboard.jsx`
- Administrative control panel (admin role only)
- Tabs: Overview, Operators, Alerts, Audit, Maintenance
- Operator management (add/delete)
- Audit log viewing
- Alert resolution tracking
- PDF report export for compliance
