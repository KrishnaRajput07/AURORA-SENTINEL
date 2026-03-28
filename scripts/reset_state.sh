#!/bin/bash

# Reset Aurora Sentinel State
# This script clears all previous analysis data, alerts, and stored videos 
# to prepare for a fresh start.

# Navigate to project root relative to script location
cd "$(dirname "$0")/.."
echo "🧹 Initializing System Reset..."

# 1. Clear Database Tables (Surgical - keeps schema and settings)
if [ -f "aurora.db" ]; then
    echo "- Clearing database records (alerts, clips)..."
    sqlite3 aurora.db "DELETE FROM alerts; DELETE FROM clip_records; VACUUM;"
else
    echo "- Database not found, skipping."
fi

# 2. Reset Metadata JSON
echo "- Resetting video analysis metadata..."
echo "[]" > storage/metadata.json

# 3. Clear Storage Directories
echo "- Cleaning storage folders (clips, processed, recordings, temp)..."
rm -rf storage/clips/* 2>/dev/null
rm -rf storage/processed/* 2>/dev/null
rm -rf storage/bin/* 2>/dev/null
rm -rf storage/recordings/* 2>/dev/null
rm -rf storage/temp/* 2>/dev/null

# 4. Reset Vector Search Database
echo "- Resetting RAG Vector Database..."
rm -rf storage/vectordb/* 2>/dev/null

echo "✅ System state reset successfully."
echo "You can now run ./start.sh for a fresh session."
