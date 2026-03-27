from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Optional, Tuple

# Optional vector DB + embedding stack (allow project to run without them).
try:
    import chromadb  # type: ignore
except Exception:
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:
    SentenceTransformer = None


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _normalize_filename(value: Optional[str]) -> str:
    return (value or "").strip()


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
            import os
            import sys

            sys.path.insert(
                0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            )
            try:
                import config

                embed_model = getattr(config, "EMBEDDING_MODEL_ID", "all-MiniLM-L6-v2")
            except ImportError:
                embed_model = "all-MiniLM-L6-v2"

            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Loading SentenceTransformer model ({embed_model}) on {device.upper()}...")
            self._model = SentenceTransformer(embed_model, device=device)
            print("Model loaded successfully.")
        return self._model

    def _upsert_document(
        self,
        doc_id: str,
        text: str,
        metadata: Dict[str, object],
    ) -> None:
        if not self._vector_enabled or self.collection is None or self.model is None:
            return
        embedding = self.model.encode(text).tolist()
        self.collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata],
        )

    def upsert_record(self, video_record):
        """
        Indexes events from a single video record (incremental).
        """
        if not self._vector_enabled or self.collection is None or self.model is None:
            # Fallback mode: no persistent vector DB; rely on metadata.json linear scan.
            return 0

        video_filename = video_record["filename"]
        video_id = video_record["id"]
        count = 0

        summary_obj = video_record.get("video_summary")
        summary_text = ""
        if isinstance(summary_obj, dict):
            summary_text = (summary_obj.get("text") or "").strip()
        elif isinstance(summary_obj, str):
            summary_text = summary_obj.strip()
        if summary_text:
            self._upsert_document(
                doc_id=f"{video_id}_summary",
                text=summary_text,
                metadata={
                    "filename": video_filename,
                    "timestamp": "-1.00",
                    "provider": "summary",
                    "severity": "info",
                    "threats": "",
                    "confidence": 0.8,
                    "is_summary": "true",
                },
            )
            count += 1

        for event in video_record.get("events", []):
            event_id = f"{video_id}_{event.get('timestamp', 0)}"
            text = (event.get("description") or "").strip()
            if not text:
                continue

            self._upsert_document(
                doc_id=event_id,
                text=text,
                metadata={
                    "filename": video_filename,
                    "timestamp": format(_safe_float(event.get("timestamp", 0)), ".2f"),
                    "provider": event.get("provider", "unknown"),
                    "severity": event.get("severity", "low"),
                    "threats": ",".join(event.get("threats", [])),
                    "confidence": event.get("confidence", 0),
                    "is_summary": "false",
                },
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

        with open(metadata_file, "r") as f:
            videos = json.load(f)

        count = 0
        for video in videos:
            count += self.upsert_record(video)

        print(f"Indexed {count} events into Vector DB.")
        return count

    def _search_vector(self, query, n_results=5, filename=None):
        if not self._vector_enabled or self.collection is None or self.model is None:
            return None

        query_embedding = self.model.encode(query).tolist()
        where_filter = {"filename": filename} if filename else None
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
        )

        hits = []
        if results.get("ids"):
            for i in range(len(results["ids"][0])):
                meta = results["metadatas"][0][i] if results.get("metadatas") else {}
                hits.append(
                    {
                        "id": results["ids"][0][i],
                        "description": results["documents"][0][i],
                        "metadata": meta,
                        "score": max(0, 1 - (results["distances"][0][i] / 1.5)),
                    }
                )
        return hits

    def _load_metadata(self, metadata_file: Optional[str] = None):
        path = metadata_file or os.getenv("METADATA_PATH", "storage/metadata.json")
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _fallback_search(self, query, n_results=5, filename=None):
        # --- Fallback search: linear scan over metadata.json (keyword-ish) ---
        videos = self._load_metadata()
        if not videos:
            return []

        q = (query or "").strip().lower()
        if not q or q == "general description":
            q_terms = []
        else:
            q_terms = [t for t in q.split() if t]

        def score_text(text: str) -> float:
            t = (text or "").lower()
            hits = sum(1 for term in q_terms if term in t)
            return min(1.0, hits / max(2, len(q_terms)))

        scored = []
        for vid in videos:
            vid_name = vid.get("filename", "unknown")
            if filename and vid_name != filename:
                continue

            summary_obj = vid.get("video_summary", {})
            if isinstance(summary_obj, dict):
                summary_text = (summary_obj.get("text") or "").strip()
            else:
                summary_text = str(summary_obj or "").strip()
            if summary_text:
                summary_score = 0.5 if not q_terms else score_text(summary_text)
                if summary_score > 0:
                    scored.append(
                        {
                            "id": f"{vid.get('id','vid')}_summary",
                            "description": summary_text,
                            "metadata": {
                                "filename": vid_name,
                                "timestamp": "-1.00",
                                "provider": "summary",
                                "severity": "info",
                                "threats": "",
                                "confidence": 0.8,
                                "is_summary": "true",
                            },
                            "score": summary_score,
                        }
                    )

            for evt in vid.get("events", []):
                desc = evt.get("description", "")
                if not q_terms:
                    s = 0.5
                else:
                    s = score_text(desc)

                if s <= 0:
                    continue
                meta = {
                    "filename": vid_name,
                    "timestamp": format(_safe_float(evt.get("timestamp", 0)), ".2f"),
                    "provider": evt.get("provider", "unknown"),
                    "severity": evt.get("severity", "low"),
                    "threats": ",".join(evt.get("threats", []) or []),
                    "confidence": evt.get("confidence", 0),
                    "is_summary": "false",
                }
                scored.append(
                    {
                        "id": f"{vid.get('id','vid')}_{evt.get('timestamp',0)}",
                        "description": desc,
                        "metadata": meta,
                        "score": s,
                    }
                )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[: int(n_results or 5)]

    def search(self, query, n_results=5, filename=None):
        """
        Semantic search for a description.
        """
        vector_hits = self._search_vector(query, n_results=n_results, filename=filename)
        if vector_hits is not None:
            return vector_hits
        return self._fallback_search(query, n_results=n_results, filename=filename)

    def get_video_record(self, filename: str) -> Optional[dict]:
        target = _normalize_filename(filename)
        if not target:
            return None
        videos = self._load_metadata()
        for vid in videos:
            if _normalize_filename(vid.get("filename")) == target:
                return vid
        return None

    def timeline_search(
        self,
        query: str,
        filename: Optional[str] = None,
        target_timestamp: Optional[float] = None,
        limit: int = 5,
    ) -> Tuple[str, List[dict]]:
        """
        Hybrid timeline retrieval:
        - semantic hits from vector/keyword search
        - lexical term overlap
        - temporal proximity to requested timestamp
        """
        videos = self._load_metadata()
        if not videos:
            return "", []

        normalized_filename = _normalize_filename(filename)
        selected_video = None
        if normalized_filename:
            selected_video = next(
                (v for v in videos if _normalize_filename(v.get("filename")) == normalized_filename),
                None,
            )

        semantic_hits = self.search(query=query, n_results=max(10, int(limit) * 3), filename=normalized_filename or None)

        if selected_video is None:
            if semantic_hits:
                best_file = _normalize_filename(semantic_hits[0].get("metadata", {}).get("filename"))
                if best_file:
                    selected_video = next(
                        (v for v in videos if _normalize_filename(v.get("filename")) == best_file),
                        None,
                    )
            if selected_video is None:
                selected_video = max(videos, key=lambda x: x.get("processed_at", ""))

        if not selected_video:
            return "", []

        events = selected_video.get("events", []) or []
        if not events:
            return selected_video.get("filename", ""), []

        q_terms = [t for t in re.findall(r"[a-zA-Z0-9]+", (query or "").lower()) if len(t) > 2]
        semantic_map: Dict[Tuple[str, float], float] = {}
        selected_name = selected_video.get("filename", "")
        for hit in semantic_hits:
            meta = hit.get("metadata", {})
            if _normalize_filename(meta.get("filename")) != _normalize_filename(selected_name):
                continue
            ts = round(_safe_float(meta.get("timestamp", 0.0)), 2)
            semantic_map[(selected_name, ts)] = max(semantic_map.get((selected_name, ts), 0.0), _safe_float(hit.get("score", 0.0)))

        ranked = []
        for evt in events:
            ts = round(_safe_float(evt.get("timestamp", 0.0)), 2)
            desc = evt.get("description", "") or ""
            lower_desc = desc.lower()

            lexical_score = 0.0
            if q_terms:
                lexical_hits = sum(1 for term in q_terms if term in lower_desc)
                lexical_score = lexical_hits / max(3, len(q_terms))

            semantic_score = semantic_map.get((selected_name, ts), 0.0)
            temporal_score = 0.0
            if target_timestamp is not None:
                distance = abs(ts - float(target_timestamp))
                temporal_score = max(0.0, 1.0 - (distance / 120.0))

            blended = (0.55 * semantic_score) + (0.25 * lexical_score) + (0.20 * temporal_score)
            ranked.append(
                {
                    "timestamp": ts,
                    "description": desc,
                    "severity": evt.get("severity", "low"),
                    "provider": evt.get("provider", "unknown"),
                    "confidence": _safe_float(evt.get("confidence", 0.0)),
                    "threats": evt.get("threats", []),
                    "score": round(blended, 4),
                }
            )

        ranked.sort(key=lambda x: x["score"], reverse=True)
        return selected_name, ranked[: max(1, int(limit))]

    def range_search(
        self,
        query: str,
        filename: str,
        start_ts: float,
        end_ts: float,
        limit: int = 5,
    ) -> List[dict]:
        """
        Retreives events within a specific [start_ts, end_ts] window.
        Uses the same hybrid scoring as timeline_search but prioritizes the range.
        """
        record = self.get_video_record(filename)
        if not record:
            return []

        events = record.get("events", []) or []
        if not events:
            return []

        # 1. Get semantic hits for the specific file
        semantic_hits = self.search(query=query, n_results=50, filename=filename)
        semantic_map: Dict[float, float] = {}
        for hit in semantic_hits:
            ts = round(_safe_float(hit.get("metadata", {}).get("timestamp", 0.0)), 2)
            semantic_map[ts] = max(semantic_map.get(ts, 0.0), _safe_float(hit.get("score", 0.0)))

        q_terms = [t for t in re.findall(r"[a-zA-Z0-9]+", (query or "").lower()) if len(t) > 2]

        ranked = []
        for evt in events:
            ts = round(_safe_float(evt.get("timestamp", 0.0)), 2)
            
            # Range filter
            if not (start_ts <= ts <= end_ts):
                continue

            desc = evt.get("description", "") or ""
            lower_desc = desc.lower()

            lexical_score = 0.0
            if q_terms:
                lexical_hits = sum(1 for term in q_terms if term in lower_desc)
                lexical_score = lexical_hits / max(3, len(q_terms))

            semantic_score = semantic_map.get(ts, 0.0)
            
            # Since it's in range, temporal score is max (1.0)
            temporal_score = 1.0

            blended = (0.55 * semantic_score) + (0.25 * lexical_score) + (0.20 * temporal_score)
            ranked.append(
                {
                    "timestamp": ts,
                    "description": desc,
                    "severity": evt.get("severity", "low"),
                    "provider": evt.get("provider", "unknown"),
                    "confidence": _safe_float(evt.get("confidence", 0.0)),
                    "score": round(blended, 4),
                }
            )

        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked[: max(1, int(limit))]

    def count_matching(self, query: str, severity: Optional[str] = None) -> dict:
        """
        Approximate global counting via vector search.
        Scans top-K results and groups by filename.
        """
        try:
            import config
            limit = getattr(config, "COUNT_SEARCH_LIMIT", 500)
        except ImportError:
            limit = 500

        hits = self.search(query=query, n_results=limit, filename=None)
        if not hits:
            return {"total_videos": 0, "total_events": 0, "videos": []}

        wanted_severity = (severity or "").strip().lower()
        grouped: Dict[str, dict] = {}
        total_events = 0

        for hit in hits:
            meta = hit.get("metadata", {})
            filename = _normalize_filename(meta.get("filename"))
            if not filename:
                continue

            hit_severity = str(meta.get("severity", "low")).lower()
            if wanted_severity and hit_severity != wanted_severity:
                continue

            total_events += 1
            group = grouped.setdefault(
                filename,
                {
                    "filename": filename,
                    "event_count": 0,
                    "best_score": 0.0,
                    "best_match": "",
                },
            )
            group["event_count"] += 1
            score = _safe_float(hit.get("score"), 0.0)
            if score > group["best_score"]:
                group["best_score"] = score
                group["best_match"] = hit.get("description", "")

        results = list(grouped.values())
        results.sort(key=lambda x: x["event_count"], reverse=True)

        return {
            "total_videos": len(results),
            "total_events": total_events,
            "videos": results[:20],  # Return top 20 videos by count
        }

    def cross_video_search(self, query: str, limit: int = 5, severity: Optional[str] = None):
        """
        Returns semantic matches grouped by filename.
        """
        hits = self.search(query=query, n_results=max(20, int(limit) * 6), filename=None)
        videos = self._load_metadata()
        summary_map = {}
        for vid in videos:
            summary_obj = vid.get("video_summary", {})
            if isinstance(summary_obj, dict):
                summary_text = (summary_obj.get("text") or "").strip()
            else:
                summary_text = str(summary_obj or "").strip()
            summary_map[_normalize_filename(vid.get("filename"))] = summary_text

        wanted_severity = (severity or "").strip().lower()
        grouped: Dict[str, dict] = {}
        for hit in hits:
            meta = hit.get("metadata", {})
            filename = _normalize_filename(meta.get("filename"))
            if not filename:
                continue

            hit_severity = str(meta.get("severity", "low")).lower()
            if wanted_severity and hit_severity != wanted_severity:
                continue

            group = grouped.setdefault(
                filename,
                {
                    "filename": filename,
                    "summary": summary_map.get(filename, ""),
                    "best_score": 0.0,
                    "events": [],
                },
            )

            score = _safe_float(hit.get("score"), 0.0)
            group["best_score"] = max(group["best_score"], score)
            group["events"].append(
                {
                    "timestamp": _safe_float(meta.get("timestamp", 0.0)),
                    "description": hit.get("description", ""),
                    "severity": meta.get("severity", "low"),
                    "provider": meta.get("provider", "unknown"),
                    "confidence": _safe_float(meta.get("confidence", 0.0)),
                    "score": score,
                }
            )

        results = list(grouped.values())
        for group in results:
            group["events"].sort(key=lambda x: x["score"], reverse=True)
            group["events"] = group["events"][: max(1, int(limit))]

        results.sort(key=lambda g: g["best_score"], reverse=True)
        return results[: max(1, int(limit))]


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
