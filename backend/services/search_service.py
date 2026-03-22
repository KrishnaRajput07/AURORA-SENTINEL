from __future__ import annotations

import os
import json
from datetime import datetime

# Optional vector DB + embedding stack (allow project to run without them).
try:
    import chromadb  # type: ignore
except Exception:
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:
    SentenceTransformer = None
class SearchService:
    def __init__(self, persistence_path="storage/vectordb"):
        print("Initializing Search Service (Lazy)...")
        self._vector_enabled = chromadb is not None and SentenceTransformer is not None
        self.client = None
        self.collection = None
        if self._vector_enabled:
            self.client = chromadb.PersistentClient(path=persistence_path)
            self.collection = self.client.get_or_create_collection(name="video_events_v2")
        self._model = None
        if self._vector_enabled:
            print("Search Service Initialized (Vector mode; model loads on first use).")
        else:
            missing = []
            if chromadb is None:
                missing.append("chromadb")
            if SentenceTransformer is None:
                missing.append("sentence-transformers")
            print(f"Search Service Initialized (Fallback mode; missing: {', '.join(missing)}).")

    @property
    def model(self):
        if not self._vector_enabled:
            return None
        if self._model is None:
            import torch
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            print(f"Loading SentenceTransformer model (all-MiniLM-L6-v2) on {device.upper()}...")
            self._model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
            print("Model loaded successfully.")
        return self._model

    def upsert_record(self, video_record):
        """
        Indexes events from a single video record (incremental).
        """
        if not self._vector_enabled or self.collection is None or self.model is None:
            # Fallback mode: no persistent vector DB; rely on metadata.json linear scan.
            return 0

        video_filename = video_record['filename']
        video_id = video_record['id']
        count = 0
        for event in video_record['events']:
            event_id = f"{video_id}_{event['timestamp']}"
            text = event['description']
            
            # Use property to ensure lazy load
            embedding = self.model.encode(text).tolist()
            
            self.collection.upsert(
                ids=[event_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[{
                    "filename": video_filename,
                    "timestamp": format(event['timestamp'], ".2f"),
                    "provider": event.get('provider', "unknown"),
                    "severity": event.get('severity', "low"),
                    "threats": ",".join(event.get('threats', [])),
                    "confidence": event.get('confidence', 0)
                }]
            )
            count += 1
        return count

    def index_metadata(self, metadata_file="storage/metadata.json"):
        """
        Reads metadata.json and indexes all events into ChromaDB.
        """
        if not self._vector_enabled or self.collection is None or self.model is None:
            # Fallback mode: no-op, metadata.json is the source of truth.
            return 0
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
                        "timestamp": format(event['timestamp'], ".2f"),  # Ensure float consistency
                        "provider": event.get('provider', "unknown"),
                        "severity": event.get('severity', "low"),
                        "threats": ",".join(event.get('threats', [])),  # Chroma doesn't support lists in metadata
                        "confidence": event.get('confidence', 0)
                    }]
                )
                count += 1
        
        print(f"Indexed {count} events into Vector DB.")
        return count

    def search(self, query, n_results=5, filename=None):
        """
        Semantic search for a description.
        """
        if self._vector_enabled and self.collection is not None and self.model is not None:
            query_embedding = self.model.encode(query).tolist()

            where_filter = {"filename": filename} if filename else None

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter
            )

            hits = []
            if results.get('ids'):
                for i in range(len(results['ids'][0])):
                    meta = results['metadatas'][0][i] if results.get('metadatas') else {}
                    hits.append({
                        "id": results['ids'][0][i],
                        "description": results['documents'][0][i],
                        "metadata": meta,
                        "score": max(0, 1 - (results['distances'][0][i] / 1.5))
                    })
            return hits

        # --- Fallback search: linear scan over metadata.json (keyword-ish) ---
        metadata_file = os.getenv("METADATA_PATH", "storage/metadata.json")
        if not os.path.exists(metadata_file):
            return []

        q = (query or "").strip().lower()
        # If query is empty or default, return everything for that file (or latest 10)
        if not q or q == "general description":
            q_terms = []
        else:
            q_terms = [t for t in q.split() if t]

        def score_text(text: str) -> float:
            t = (text or "").lower()
            hits = sum(1 for term in q_terms if term in t)
            # Normalize into 0..1 range
            return min(1.0, hits / max(2, len(q_terms)))

        try:
            with open(metadata_file, "r") as f:
                videos = json.load(f)
        except Exception:
            return []

        scored = []
        for vid in videos:
            vid_name = vid.get("filename", "unknown")
            if filename and vid_name != filename:
                continue
            for evt in vid.get("events", []):
                desc = evt.get("description", "")
                if not q_terms:
                    s = 0.5 # Default score for "everything" view
                else:
                    s = score_text(desc)
                
                if s <= 0:
                    continue
                meta = {
                    "filename": vid_name,
                    "timestamp": format(float(evt.get("timestamp", 0)), ".2f"),
                    "provider": evt.get("provider", "unknown"),
                    "severity": evt.get("severity", "low"),
                    "threats": ",".join(evt.get("threats", []) or []),
                    "confidence": evt.get("confidence", 0),
                }
                scored.append({
                    "id": f"{vid.get('id','vid')}_{evt.get('timestamp',0)}",
                    "description": desc,
                    "metadata": meta,
                    "score": s,
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[: int(n_results or 5)]

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
