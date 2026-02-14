import chromadb
from sentence_transformers import SentenceTransformer
import os
import json
from datetime import datetime

class SearchService:
    def __init__(self, persistence_path="storage/vectordb"):
        print("Initializing Search Service...")
        self.client = chromadb.PersistentClient(path=persistence_path)
        self.collection = self.client.get_or_create_collection(name="video_events")
        
        # Load reliable, small embedding model
        # invalidates 4GB VRAM constraint if run on GPU alongside Ollama?
        # We run this on CPU to be safe.
        self.model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu') 
        print("Search Service Ready.")

    def index_metadata(self, metadata_file="storage/metadata.json"):
        """
        Reads metadata.json and indexes all events into ChromaDB.
        """
        if not os.path.exists(metadata_file):
            print("No metadata to index.")
            return 0

        with open(metadata_file, 'r') as f:
            videos = json.load(f)

        count = 0
        for video in videos:
            video_filename = video['filename']
            for event in video['events']:
                # Create a unique ID for each event
                event_id = f"{video['id']}_{event['timestamp']}"
                
                # Check if already indexed (naive check, usually Chroma handles dupes by ID)
                # We'll just upsert.
                
                text = event['description']
                embedding = self.model.encode(text).tolist()
                
                self.collection.upsert(
                    ids=[event_id],
                    embeddings=[embedding],
                    documents=[text],
                    metadatas=[{
                        "filename": video_filename,
                        "timestamp": event['timestamp'],
                        "provider": event['provider'] or "unknown"
                    }]
                )
                count += 1
        
        print(f"Indexed {count} events into Vector DB.")
        return count

    def search(self, query, n_results=5):
        """
        Semantic search for a description.
        """
        query_embedding = self.model.encode(query).tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        hits = []
        if results['ids']:
            for i in range(len(results['ids'][0])):
                hits.append({
                    "id": results['ids'][0][i],
                    "description": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    # Chroma returns L2 distance by default (smaller is better).
                    # Convert to similarity score (0 to 1).
                    # A distance of 0 means identical. A distance of >1.5 is usually unrelated.
                    # Simple heuristic: score = 1 - (distance / 2) clamped to 0
                    "score": max(0, 1 - (results['distances'][0][i] / 1.8))
                })
        
        return hits

# Singleton
search_service = SearchService()

if __name__ == "__main__":
    # Add project root to path for standalone execution
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    print("Indexing metadata...")
    search_service.index_metadata()
    print("Test Search: 'fight'")
    res = search_service.search("fight")
    for r in res:
        print(f"  [{r['score']:.2f}] {r['description'][:50]}...")
