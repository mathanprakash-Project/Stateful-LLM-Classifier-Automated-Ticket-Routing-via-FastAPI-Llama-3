import logging
import math
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    HAS_VECTOR_DEPS = True
except ImportError:
    HAS_VECTOR_DEPS = False
    logger.warning("sentence-transformers or numpy not installed. Vector search disabled.")

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25_DEPS = True
except ImportError:
    HAS_BM25_DEPS = False
    logger.warning("rank_bm25 not installed. BM25 search disabled.")

class HybridRetriever:
    def __init__(self):
        self.documents = []
        self.doc_embeddings = []
        self.model = None
        
        if HAS_VECTOR_DEPS:
            try:
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                logger.error(f"Failed to load sentence transformer model: {e}")
                self.model = None
                
        self.bm25 = None

    def embed_text(self, text: str) -> List[float]:
        if not self.model or not HAS_VECTOR_DEPS:
            return []
        try:
            return self.model.encode(text).tolist()
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            return []

    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any], category: str) -> None:
        doc = {
            "id": doc_id,
            "content": content,
            "metadata": metadata,
            "category": category
        }
        self.documents.append(doc)
        
        if self.model and HAS_VECTOR_DEPS:
            embedding = self.embed_text(content)
            self.doc_embeddings.append(embedding)
            
        if HAS_BM25_DEPS and self.documents:
            # Rebuild BM25 index on every add for simplicity
            tokenized_corpus = [d["content"].lower().split() for d in self.documents]
            self.bm25 = BM25Okapi(tokenized_corpus)

    def vector_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        if not HAS_VECTOR_DEPS or not self.doc_embeddings or not query_embedding:
            return []
            
        try:
            query_vec = np.array(query_embedding)
            doc_vecs = np.array(self.doc_embeddings)
            
            # Cosine similarity
            norms = np.linalg.norm(doc_vecs, axis=1) * np.linalg.norm(query_vec)
            # Avoid division by zero
            norms[norms == 0] = 1e-10
            similarities = np.dot(doc_vecs, query_vec) / norms
            
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                doc = self.documents[idx].copy()
                doc["score"] = float(similarities[idx])
                results.append(doc)
                
            return results
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []

    def bm25_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.documents:
            return []
            
        if HAS_BM25_DEPS and self.bm25:
            try:
                tokenized_query = query.lower().split()
                scores = self.bm25.get_scores(tokenized_query)
                top_indices = np.argsort(scores)[::-1][:top_k]
                results = []
                for idx in top_indices:
                    if scores[idx] > 0:
                        doc = self.documents[idx].copy()
                        doc["score"] = float(scores[idx])
                        results.append(doc)
                if results:
                    return results
            except Exception as e:
                logger.error(f"Error in BM25 search: {e}")

        # Deterministic token overlap fallback (works without external C/ML dependencies)
        query_tokens = set(query.lower().split())
        scored = []
        for doc in self.documents:
            content_tokens = set(doc["content"].lower().split())
            overlap = len(query_tokens.intersection(content_tokens))
            if overlap > 0:
                d = doc.copy()
                d["score"] = float(overlap)
                scored.append(d)
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def _compute_rrf(self, vector_results: List[Dict[str, Any]], bm25_results: List[Dict[str, Any]], k: int = 60, vector_weight: float = 0.7, bm25_weight: float = 0.3) -> List[Dict[str, Any]]:
        scores = {}
        doc_map = {}
        
        # Rank vector results
        for rank, doc in enumerate(vector_results):
            doc_id = doc["id"]
            if doc_id not in scores:
                scores[doc_id] = 0.0
                doc_map[doc_id] = doc
            scores[doc_id] += vector_weight * (1.0 / (k + rank + 1))
            
        # Rank BM25 results
        for rank, doc in enumerate(bm25_results):
            doc_id = doc["id"]
            if doc_id not in scores:
                scores[doc_id] = 0.0
                doc_map[doc_id] = doc
            scores[doc_id] += bm25_weight * (1.0 / (k + rank + 1))
            
        # Sort by RRF score
        sorted_docs = sorted([(doc_id, score) for doc_id, score in scores.items()], key=lambda x: x[1], reverse=True)
        
        results = []
        for doc_id, score in sorted_docs:
            doc = doc_map[doc_id].copy()
            doc["rrf_score"] = score
            results.append(doc)
            
        return results

    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.embed_text(query)
        
        vector_results = self.vector_search(query_embedding, top_k=top_k)
        bm25_results = self.bm25_search(query, top_k=top_k)
        
        rrf_results = self._compute_rrf(vector_results, bm25_results)
        
        return rrf_results[:top_k]

# Global instance for app usage
global_retriever = HybridRetriever()
_seeded = False

def get_retriever() -> HybridRetriever:
    global _seeded
    if not _seeded:
        _seeded = True
        try:
            from app.core.knowledge_base import seed_knowledge_base
            seed_knowledge_base(global_retriever)
        except Exception as e:
            logger.error("Failed to seed knowledge base: %s", e)
    return global_retriever

