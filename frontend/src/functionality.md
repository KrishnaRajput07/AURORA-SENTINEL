# Frontend Source — Functionality

This directory contains the complete React frontend application for AURORA Sentinel.

## Architecture
- **Framework**: React 18 with functional components and hooks
- **UI Library**: Material-UI (MUI) v5 with custom theme
- **Routing**: React Router v6 with protected routes
- **State**: React Context API for global state, local state for components
- **Animations**: Framer Motion for transitions and effects
- **Icons**: Lucide React
- **Charts**: Recharts
- **Maps**: Leaflet with React-Leaflet

## Key Files

### `App.js`
- Root application component
- Sets up ThemeProvider, CssBaseline, and all context providers (Auth, Notification, Settings, Intelligence)
- Defines route structure with ProtectedRoute wrapper
- Roles: operator (standard access), admin (full access)

### `config.js`
- Environment-based API configuration
- `API_BASE_URL`: Points to localhost:8000 in dev, relative in production
- `WS_BASE_URL`: WebSocket URL with protocol detection (ws/wss)

### `index.js`
- React application entry point
- BrowserRouter with future flags for v7 compatibility
- Service worker force-unregistration to prevent stale cache issues

### `index.css`
- Global CSS styles
- Font imports, base styling

### `theme.js`
- Custom MUI theme with AURORA Sentinel color palette:
  - Primary: Sage Green (#6F8F72)
  - Secondary: Terracotta (#F2A65A)
  - Background: Beige (#E8E2D8)
  - Paper: White
  - Text: Deep Black/Green (#2C3333)
- Typography: Inter font family
- Component overrides for Paper, Button, AppBar, Tab, Chip

## Sub-directories

| Directory | Purpose |
|-----------|---------|
| `assets/` | Static image files (logos, mascot) |
| `components/` | Reusable UI components (14 main components + tests + ui) |
| `context/` | React context providers for global state |
| `pages/` | Page-level route components |

## Routes
| Path | Page | Access |
|------|------|--------|
| `/` | LandingPage | Public |
| `/login` | Login | Public |
| `/dashboard` | Dashboard | Operator+ |
| `/surveillance` | LiveSurveillance | Operator+ |
| `/intelligence` | Intelligence | Operator+ |
| `/archives` | Archives | Operator+ |
| `/alerts` | Alerts | Operator+ |
| `/analytics` | Analytics | Operator+ |
| `/system` | System | Operator+ |
| `/admin` | AdminDashboard | Admin only |
