# Aurora Sentinel 🛡️

**Aurora Sentinel** is an advanced intelligent video analytics and surveillance platform designed for real-time threat detection and situational awareness. It leverages state-of-the-art computer vision models (YOLOv8) to provide actionable insights through a modern, responsive dashboard.

## 🚀 Features

- **Real-Time Detection**: Utilization of YOLOv8 for object detection and pose estimation.
- **Interactive Dashboard**: A modern frontend built with React and Material UI for monitoring live feeds and analytics.
- **Geospatial Intelligence**: Integrated map visualizations using Leaflet for spatial awareness of deployed sensors/cameras.
- **Live Analytics**: Real-time charts and data visualization using Recharts and Socket.io.
- **Robust Backend**: Scalable FastAPI backend with PostgreSQL for data persistence and Redis for caching/messaging.
- **Video Processing**: Efficient video stream handling with FFmpeg and MoviePy.

## 🛠️ Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **ML/CV**: [PyTorch](https://pytorch.org/), [Ultralytics YOLOv8](https://docs.ultralytics.com/), OpenCV
- **Database**: PostgreSQL (via SQLAlchemy), Redis
- **Language**: Python 3.10+

### Frontend
- **Framework**: [React](https://react.dev/)
- **UI Library**: Material UI (MUI), Lucide React
- **Maps**: Leaflet (React-Leaflet)
- **State/Data**: Axios, Socket.io-client
- **Visualization**: Recharts, Framer Motion

## 🏁 Getting Started

### Prerequisites
- [Docker & Docker Compose](https://www.docker.com/) (Recommended)
- OR
- Python 3.10+
- Node.js & npm
- PostgreSQL & Redis (running locally)

### 🐳 run with Docker (Recommended)

The easiest way to get up and running is using Docker Compose.

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd AURORA-SENTINEL
   ```

2. **Start the services**:
   ```bash
   docker-compose up --build
   ```

   This will start:
   - **Backend API**: `http://localhost:8000`
   - **Frontend Dashboard**: `http://localhost:3000` (mapped if configured, or access via API for now)
   - **PostgreSQL**: Port 5432
   - **Redis**: Port 6379

3. **Access Documentation**:
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 💻 Run Locally (Windows/PowerShell)

A convenience script `start.ps1` is provided for Windows users.

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the startup script**:
   ```powershell
   ./start.ps1
   ```
   This script will:
   - Launch the Backend API (`uvicorn`).
   - Install Frontend dependencies (if missing).
   - Launch the Frontend Dashboard (`npm start`).

   *Note: Ensure you have a local PostgreSQL and Redis instance running if not using Docker, and update the environment variables in `docker-compose.yml` or create a `.env` file reflecting your local config.*

## 📂 Project Structure

```
AURORA-SENTINEL/
├── backend/                # FastAPI application
│   ├── api/               # API routes and controllers
│   ├── services/          # Business logic & ML inference
│   ├── video/             # Video processing modules
│   └── ...
├── frontend/               # React application
│   ├── public/
│   └── src/
├── data/                   # Data storage
├── models/                 # YOLOv8 model weights (.pt files)
├── docker-compose.yml      # Container orchestration
├── Dockerfile              # Backend container definition
├── requirements.txt        # Python dependencies
└── start.ps1               # Local startup script
```
