"""
Embedding function for the RAG retrieval layer.

Primary path: sentence-transformers ('all-MiniLM-L6-v2') if it's installed
and able to download its model (needs one-time internet access to Hugging
Face). Use this in a real deployment for better retrieval quality.

Fallback path: a TF-IDF vectorizer (scikit-learn) fitted on the document
corpus. No model download, no native/compiled vector-database dependency --
just numpy arrays -- so it is the most portable option and works
identically on Windows, macOS, and Linux with no external services.

This module intentionally has NO dependency on ChromaDB or any other
native-extension vector database, after repeated silent crashes were
observed with that combination on some Windows setups (crash with no
Python traceback, consistent with a native/C-extension fault rather than
an application bug). Retrieval here is done with plain numpy cosine
similarity in rag/pipeline.py instead.
"""
from typing import List
import numpy as np


class SentenceTransformerEmbedding:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> np.ndarray:
        return np.array(self.model.encode(texts))

    def name(self) -> str:
        return "sentence_transformer_embedding"


class TfidfEmbedding:
    """Lightweight fallback with no external model download and no native
    vector-database dependency required."""

    def __init__(self, corpus: List[str]):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer(max_features=512)
        self.vectorizer.fit(corpus)

    def embed(self, texts: List[str]) -> np.ndarray:
        return self.vectorizer.transform(texts).toarray()

    def name(self) -> str:
        return "tfidf_embedding"


def get_embedding_function(corpus: List[str] = None):
    try:
        return SentenceTransformerEmbedding()
    except Exception as e:
        print(f"[rag.embeddings] sentence-transformers unavailable ({e.__class__.__name__}); "
              f"falling back to TF-IDF embeddings.")
        if corpus is None:
            raise ValueError("TF-IDF fallback requires a corpus to fit on.")
        return TfidfEmbedding(corpus)
