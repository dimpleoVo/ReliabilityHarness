import logging
from reliability_harness.core.rag import RAG_Engine

logger = logging.getLogger(__name__)


class FailureMemoryVectorStore:
    def __init__(self):
        self.rag = RAG_Engine(collection_name="reactx_failure_memory")

    def build_text(self, item: dict) -> str:
        return f"""Task:
{item["task"]}

Bad Code:
{item["bad_code"]}

Bad Observation:
{item.get("bad_output", "")}

Fixed Code:
{item["fixed_code"]}

Fixed Observation:
{item.get("fixed_output", "")}
"""

    def add(self, item: dict):
        text = self.build_text(item)
        meta = item.get("meta") or {}
        self.rag.add_documents(
            documents=[text],
            metadatas=[{
                "task": str(item.get("task", "")),
                "error_type": str(item.get("error_type", "")),
                "bad_code": str(item.get("bad_code", "")),
                "bad_output": str(item.get("bad_output", "")),
                "stderr": str(item.get("bad_stderr", "")),
                "fixed_code": str(item.get("fixed_code", "")),
                "fixed_output": str(item.get("fixed_output", "")),
                "score_before": str(meta.get("score_before", "")),
                "score_after": str(meta.get("score_after", "")),
            }]
        )

    def _parse_chroma_native(self, raw: dict) -> list[dict]:
        """Native Chroma collection.query() format: {documents: [[...]], metadatas: [[...]], distances: [[...]]}"""
        docs = (raw.get("documents") or [[]])[0]
        metas = (raw.get("metadatas") or [[]])[0]
        results = []
        for i, doc in enumerate(docs):
            m = metas[i] if i < len(metas) else {}
            results.append({
                "task": m.get("task", ""),
                "bad_code": m.get("bad_code", ""),
                "bad_output": m.get("bad_output", ""),
                "stderr": m.get("stderr", ""),
                "fixed_code": m.get("fixed_code", ""),
                "fixed_output": m.get("fixed_output", ""),
                "score_before": m.get("score_before", ""),
                "score_after": m.get("score_after", ""),
                "source": doc or "",
            })
        return results

    def _parse_rag_engine(self, raw: dict) -> list[dict]:
        """RAG_Engine.search() format: {query: ..., results: [...], distances: [...]}"""
        docs = raw.get("results") or []
        return [
            {
                "task": "",
                "bad_code": "",
                "bad_output": "",
                "stderr": "",
                "fixed_code": "",
                "fixed_output": "",
                "score_before": "",
                "score_after": "",
                "source": doc or "",
            }
            for doc in docs
        ]

    def search(self, query: str, top_k: int = 2) -> list[dict]:
        try:
            raw = self.rag.collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            logger.warning(f"[Memory] Chroma query failed: {e}")
            print("[Memory] No similar failure-fix examples retrieved")
            return []

        if "documents" in raw:
            results = self._parse_chroma_native(raw)
        elif "results" in raw:
            results = self._parse_rag_engine(raw)
        else:
            results = []

        if results:
            print(f"[Memory] Retrieved {len(results)} similar failure-fix examples")
        else:
            print("[Memory] No similar failure-fix examples retrieved")

        return results