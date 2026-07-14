"""
FAISS Vector Store adapter with pure-Python in-memory search fallback.
"""

import os
import pickle
from typing import Any, Dict, List

import numpy as np

from core.config import get_settings
from adapters.vectorstore.base import BaseVectorStore

try:
    import faiss
except ImportError:
    faiss = None

settings = get_settings()


class FAISSAdapter(BaseVectorStore):
    """
    Concrete adapter utilizing FAISS for indexing.
    Falls back to a serialized NumPy cosine-similarity memory index if
    binary faiss package is unavailable.
    """

    def __init__(self):
        self.storage_dir = settings.vector_store_path
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_index_paths(self, project_id: str) -> tuple[str, str]:
        """Returns the files mapped to a namespace."""
        index_file = os.path.join(self.storage_dir, f"{project_id}.index")
        meta_file = os.path.join(self.storage_dir, f"{project_id}.meta")
        return index_file, meta_file

    def add_documents(self, project_id: str, documents: List[Dict[str, Any]]) -> None:
        if not documents:
            return

        index_file, meta_file = self._get_index_paths(project_id)
        
        # Load existing data
        existing_meta = []
        existing_embeddings = []
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "rb") as f:
                    existing_meta = pickle.load(f)
            except Exception:
                existing_meta = []

        new_embeddings = [doc["embedding"] for doc in documents]
        new_meta = [{
            "id": doc["id"],
            "text": doc["text"],
            "metadata": doc.get("metadata", {})
        } for doc in documents]

        # Combine
        combined_meta = existing_meta + new_meta
        
        if faiss:
            # Concrete FAISS implementation
            dimension = len(new_embeddings[0])
            # Load existing FAISS index or create
            if os.path.exists(index_file):
                try:
                    index = faiss.read_index(index_file)
                except Exception:
                    index = faiss.IndexFlatIP(dimension)  # Cosine dot-product
            else:
                index = faiss.IndexFlatIP(dimension)

            arr = np.array(new_embeddings, dtype=np.float32)
            # Normalize vectors for cosine dot-product
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            arr = np.where(norms > 0, arr / norms, arr)
            
            index.add(arr)
            faiss.write_index(index, index_file)
        else:
            # Fallback numpy index
            if os.path.exists(index_file):
                try:
                    with open(index_file, "rb") as f:
                        existing_embeddings = pickle.load(f)
                except Exception:
                    existing_embeddings = []
            
            combined_embeddings = existing_embeddings + new_embeddings
            with open(index_file, "wb") as f:
                pickle.dump(combined_embeddings, f)

        # Write metadata
        with open(meta_file, "wb") as f:
            pickle.dump(combined_meta, f)

    def search(
        self, 
        project_id: str, 
        query_embedding: List[float], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        index_file, meta_file = self._get_index_paths(project_id)

        if not os.path.exists(meta_file) or not os.path.exists(index_file):
            return []

        try:
            with open(meta_file, "rb") as f:
                metadata_list = pickle.load(f)
        except Exception:
            return []

        q_arr = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_arr)
        if q_norm > 0:
            q_arr = q_arr / q_norm

        if faiss:
            try:
                index = faiss.read_index(index_file)
                # Query index
                distances, indices = index.search(np.expand_dims(q_arr, axis=0), top_k)
                
                results = []
                for score, idx in zip(distances[0], indices[0]):
                    if idx != -1 and idx < len(metadata_list):
                        meta = metadata_list[idx]
                        results.append({
                            "id": meta["id"],
                            "text": meta["text"],
                            "score": float(score),
                            "metadata": meta["metadata"]
                        })
                return results
            except Exception:
                pass  # Fallback on search failure

        # Fallback pure-Python/numpy cosine search
        try:
            with open(index_file, "rb") as f:
                embeddings_list = pickle.load(f)
        except Exception:
            return []

        if not embeddings_list:
            return []

        arr = np.array(embeddings_list, dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        arr = np.where(norms > 0, arr / norms, arr)

        # Dot product
        similarities = np.dot(arr, q_arr)
        
        # Get top K indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            meta = metadata_list[idx]
            results.append({
                "id": meta["id"],
                "text": meta["text"],
                "score": score,
                "metadata": meta["metadata"]
            })
        return results

    def clear_project_namespace(self, project_id: str) -> None:
        index_file, meta_file = self._get_index_paths(project_id)
        for f in (index_file, meta_file):
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass


# Singleton adapter
vector_store = FAISSAdapter()
