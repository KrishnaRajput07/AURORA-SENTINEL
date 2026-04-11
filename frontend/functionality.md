# Frontend — Functionality

The frontend is a React-based single-page application (SPA) that provides the user interface for surveillance operators and administrators.

## Structure

| Path | Contents |
|------|----------|
| `public/` | Static assets (HTML template, logo, manifest) |
| `src/` | React application source code |
| `package.json` | NPM dependencies and scripts |
| `package-lock.json` | Locked dependency versions |

## Build Process
- **Development**: `npm start` — runs dev server on localhost:3000 with hot reload
- **Production**: `npm run build` — creates optimized build in `build/` directory
- **Integration**: Backend serves the `build/` directory via FastAPI static files

## Key Features
1. **Real-time surveillance**: WebSocket-connected live feed with ML overlay
2. **Alert management**: Acknowledge, resolve, and track security incidents
3. **Intelligence hub**: Upload videos, search events, AI-powered chatbot
4. **Archive browser**: View, play, and manage recorded clips
5. **System monitoring**: Health checks, performance settings, operator management
6. **Role-based access**: Separate interfaces for operators and administrators

## Dependencies (selected)
- `@mui/material` — UI component library
- `react-router-dom` — Client-side routing
- `framer-motion` — Animations and transitions
- `lucide-react` — Icon set
- `recharts` — Data visualization
- `react-leaflet` — Interactive maps
- `react-dropzone` — File upload drag-and-drop
- `jspdf` + `jspdf-autotable` — PDF report generation
- `date-fns` — Date formatting

## Theming
- Custom MUI theme with nature-inspired palette (sage green, terracotta, beige)
- Responsive design with mobile breakpoints
- Dark mode ready (currently light mode only)
