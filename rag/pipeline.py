"""
RAG pipeline for the AI Business Analyst / Executive Copilot.

- Chunks synthetic business documents
- Embeds them (sentence-transformers if available, TF-IDF fallback otherwise)
- Stores the resulting vectors in memory as a plain numpy array
- Retrieves top-k relevant chunks for a query using cosine similarity
- Synthesizes an answer: uses an LLM (OpenAI, via LangChain) if
  OPENAI_API_KEY is set, otherwise falls back to an extractive summary of
  the retrieved chunks -- so the pipeline is fully runnable and demoable
  even without any API key or paid access.

Deliberately has NO vector-database dependency (no ChromaDB, no FAISS).
For a corpus of a handful of documents / a few hundred chunks, an in-memory
numpy similarity search is more than fast enough, and removes an entire
class of native-extension crashes seen with vector-DB libraries on some
Windows setups. For a much larger corpus in a real deployment, swap
retrieve() below for a real vector database -- the rest of the pipeline
does not need to change.
"""
import os
import numpy as np
from dotenv import load_dotenv

from rag.documents import DOCUMENTS
from rag.embeddings import get_embedding_function

load_dotenv()


def chunk_text(text: str, chunk_size: int = 120, overlap: int = 20):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        chunks.append(" ".join(words[start:start + chunk_size]))
        start += chunk_size - overlap
    return chunks


def cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    query_norm = np.linalg.norm(query_vec) + 1e-10
    matrix_norms = np.linalg.norm(matrix, axis=1) + 1e-10
    return (matrix @ query_vec) / (matrix_norms * query_norm)


class RagPipeline:
    def __init__(self, documents=None):
        self.documents = documents or DOCUMENTS
        all_chunks = []
        for doc in self.documents:
            all_chunks.extend(chunk_text(doc))
        self.chunks = all_chunks

        self.embedder = get_embedding_function(corpus=self.chunks)
        self.chunk_vectors = self.embedder.embed(self.chunks)

    def retrieve(self, query: str, k: int = 3):
        query_vec = self.embedder.embed([query])[0]
        sims = cosine_similarity(query_vec, self.chunk_vectors)
        top_idx = np.argsort(sims)[::-1][:k]
        return [(self.chunks[i], float(max(0.0, sims[i]))) for i in top_idx]

    def answer(self, query: str, k: int = 3) -> dict:
        retrieved = self.retrieve(query, k=k)
        sources = [{"chunk": doc[:220] + ("..." if len(doc) > 220 else ""), "confidence": round(conf, 2)}
                   for doc, conf in retrieved]

        if os.getenv("OPENAI_API_KEY"):
            answer_text = self._llm_answer(query, [doc for doc, _ in retrieved])
        else:
            answer_text = self._extractive_answer(retrieved)

        avg_confidence = round(sum(c for _, c in retrieved) / len(retrieved), 2) if retrieved else 0.0

        return {"query": query, "answer": answer_text, "confidence": avg_confidence, "sources": sources}

    def _llm_answer(self, query: str, context_chunks: list) -> str:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        context = "\n\n".join(context_chunks)
        prompt = (
            "You are a business analyst. Using ONLY the context below, answer the "
            "executive's question concisely, in 2-4 sentences.\n\n"
            f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
        )
        return llm.invoke(prompt).content

    def _extractive_answer(self, retrieved: list) -> str:
        """No-LLM fallback: surfaces the most relevant chunk directly,
        clearly labeled, so the system stays explainable without API access."""
        if not retrieved:
            return "No relevant information found in available documents."
        top_chunk, conf = retrieved[0]
        return (f"[Extractive summary - no LLM configured] Most relevant document "
                f"section (confidence {conf:.2f}): {top_chunk}")


_PIPELINE_SINGLETON = None


def get_pipeline():
    global _PIPELINE_SINGLETON
    if _PIPELINE_SINGLETON is None:
        _PIPELINE_SINGLETON = RagPipeline()
    return _PIPELINE_SINGLETON


if __name__ == "__main__":
    pipeline = get_pipeline()
    for q in ["Why did sales decrease in some branches?",
              "Which products should we consider discontinuing?",
              "What is driving customer support ticket volume?"]:
        result = pipeline.answer(q)
        print(f"\nQ: {q}")
        print(f"A: {result['answer']}")
        print(f"Confidence: {result['confidence']}")
