# app/eval/boundary_analyzer.py

from typing import List, Dict, Any


class BoundaryAnalyzer:
    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析不同 slice 的 failure 边界
        """

        slice_stats = {}

        for r in history:
            doc_type = r.get("meta", {}).get("doc_type", "unknown")
            error_type = r.get("error_type", "normal")

            if doc_type not in slice_stats:
                slice_stats[doc_type] = {"total": 0, "errors": 0}

            slice_stats[doc_type]["total"] += 1

            if error_type != "normal":
                slice_stats[doc_type]["errors"] += 1

        boundary = {}

        for doc_type, stats in slice_stats.items():
            error_rate = stats["errors"] / stats["total"]

            boundary[doc_type] = {
                "error_rate": error_rate,
                "total": stats["total"]
            }

        return boundary