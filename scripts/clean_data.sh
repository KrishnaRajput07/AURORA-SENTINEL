#!/bin/bash

# Navigate to the project directory from the scripts folder
cd "$(dirname "$0")/.."

echo "🧹 Cleaning up Aurora Sentinel Intelligence Data..."

echo "- Removing temporary video uploads..."
rm -rf storage/temp/*

echo "- Removing processed video outputs..."
rm -rf storage/processed/*

echo "- Removing highly-secured archived threat videos..."
rm -rf storage/bin/*

echo "- Resetting intelligence metadata search index..."
echo "[]" > storage/metadata.json

echo "- Resetting SQLite local database..."
if [ -f "aurora.db" ]; then
    rm aurora.db
fi

echo "✅ Cleanup complete! All folders are empty and databases are reset."
echo "The system will automatically recreate the database file the next time you run start.sh."
