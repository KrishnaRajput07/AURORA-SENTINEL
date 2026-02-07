from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from datetime import datetime

router = APIRouter()
STORAGE_PATH = "storage/clips"
BIN_PATH = "storage/bin"

@router.get("/list")
async def list_archives(source: str = "active"):
    path = STORAGE_PATH if source == "active" else BIN_PATH
    if not os.path.exists(path):
        return {"clips": []}
    
    files = []
    for f in os.listdir(path):
        if f.endswith(".mp4"):
            f_path = os.path.join(path, f)
            stat = os.stat(f_path)
            files.append({
                "id": f,
                "name": f,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "url": f"/archive/download/{f}?source={source}"
            })
    
    # Sort by newest first
    files.sort(key=lambda x: x["created_at"], reverse=True)
    return {"clips": files}

@router.get("/download/{filename}")
async def download_clip(filename: str, source: str = "active"):
    path = STORAGE_PATH if source == "active" else BIN_PATH
    file_path = os.path.join(path, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Clip not found")
        
    return FileResponse(file_path, media_type="video/mp4")
