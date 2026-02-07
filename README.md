# Aurora Sentinel 🛡️

**Next-Gen AI Surveillance & Threat Detection System**

Aurora Sentinel is an advanced surveillance system providing real-time threat detection, behavioral analytics, and privacy-preserving object tracking. It leverages computer vision and AI to enhance security operations while respecting individual privacy.

![Dashboard Preview](frontend/public/dashboard-preview.png)

## 🚀 Key Features

### 1. 📹 Live Intelligent Surveillance
- **Real-Time Video Stream**: Low-latency WebSocket streaming for live camera feeds.
- **Object Detection**: Identifies critical objects (Persons, Backpacks, Suitcases) using YOLOv8.
- **Persistent Tracking**: Tracks unique individuals across frames (CPU-optimized ByteTrack logic).
- **Privacy Anonymizer**: Automatically blurs faces or converts bodies to skeletons to protect identity while maintaining behavioral context.

### 2. 🧠 AI & Risk Analytics
- **Behavioral Analysis**: Detects aggressive postures (fighting stance, hands up) based on pose estimation.
- **Risk Scoring Engine**: Calculates dynamic threat levels (0-100%) based on multiple factors:
  - Aggression detection
  - Proximity violations (crowding/fighting)
  - Loitering detection
  - Unattended object detection
  - Crowd density analysis
  - Contextual awareness (Time/Location)
- **Automatic Adjustments**: Tunable weights for different risk factors.

### 3. 🚨 Alert System
- **Real-Time Alerts**: Generates alerts (Low, Medium, High, Critical) when risk thresholds are breached.
- **Dashboard Notifications**: Immediate visual feedback on the operator dashboard.
- **Database Logging**: Stores all alerts with timestamp, risk score, and contributing factors for audit.

### 4. 📊 Command Dashboard
- **Interactive Map**: Visualizes camera locations (Leaflet integration).
- **Live Metrics**: Displays real-time person count, object count, and threat levels.
- **System Health**: Monitors backend status and model loading.

## 🛠️ Technology Stack

- **Frontend**: React 19, Material UI, Recharts, Framer Motion, Leaflet
- **Backend**: FastAPI (Python 3.13), WebSocket
- **AI/ML**: 
  - **PyTorch & Ultralytics YOLOv8** (Object & Pose Detection)
  - **OpenCV** (Image Processing)
  - **Haar Cascades** (Face Detection)
- **Database**: PostgreSQL (Production) / SQLite (Dev Fallback)
- **DevOps**: Docker support included

## ⚡ Getting Started

### Prerequisites
- Python 3.10+ (Tested on 3.13)
- Node.js 16+

### Quick Start
We provide a unified startup script for Windows.

1. **Clone the repository**
2. **Run the Startup Script**:
   ```powershell
   .\start.ps1
   ```
   This script will:
   - Install backend dependencies (requirements.txt) if missing.
   - Install frontend dependencies (node_modules) if missing.
   - Launch the FastAPI backend server (Port 8000).
   - Launch the React frontend (Port 3000).

3. **Access the Dashboard**:
   - Open your browser to `http://localhost:3000`
   - Allow camera permissions when prompted.

### Troubleshooting (Windows)
- **Camera Feed Fails**: If you see a connection error or the camera stops:
  - The system is optimized for CPU usage on Windows to avoid GPU driver crashes.
  - Restart the app using `.\start.ps1`.
- **Backend Crash**: The system includes auto-recovery logic for frame processing. Check the terminal for detailed error logs.

## 📁 Project Structure

```
AURORA-SENTINEL/
├── backend/
│   ├── api/            # FastAPI Routers & Endpoints
│   ├── models/         # AI Models (Detection, Scoring, Privacy)
│   ├── services/       # ML Service Singleton
│   └── db/             # Database Schemas & Connection
├── frontend/
│   ├── src/
│   │   ├── components/ # Dashboard Widgets & Live Feed
│   │   └── pages/      # Main Layouts
│   └── public/
└── start.ps1           # Main Launcher Script
```

## 🛡️ Privacy & Ethics
Aurora Sentinel is designed with "Privacy by Default". 
- Facial blurring is enabled strictly for privacy protection.
- Skeleton tracking mode removes all visual identity features while preserving behavioral data.

---
*Built for the 2024 AI Security Hackathon*
