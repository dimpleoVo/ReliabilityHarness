"""
Code extractor for generation-only LLM responses.

Extracts Python code from fenced code blocks in raw LLM output.
No side effects. No LLM calls. No external dependencies.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional


ExtractionStatus = Literal["success", "no_code_block", "empty_response", "error"]


@dataclass
class CodeExtractionResult:
    extracted_code: Optional[str]
    extraction_status: ExtractionStatus
    error: Optional[str] = None


# ```python ... ``` block (tried first — preferred over generic fence)
_PYTHON_FENCE_RE = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)

# generic ``` ... ``` block (fallback when no python-labelled block present)
_GENERIC_FENCE_RE = re.compile(r"```\s*\n(.*?)```", re.DOTALL)


def extract_python_code(raw_response: str) -> CodeExtractionResult:
    """Extract Python code from a fenced code block in raw LLM output.

    Tries ```python first, then generic ```. Does not add print() calls or
    modify function logic. Does not call code_sanitizer.
    """
    if not raw_response or not raw_response.strip():
        return CodeExtractionResult(
            extracted_code=None,
            extraction_status="empty_response",
        )

    m = _PYTHON_FENCE_RE.search(raw_response)
    if m:
        return CodeExtractionResult(
            extracted_code=m.group(1).rstrip(),
            extraction_status="success",
        )

    m = _GENERIC_FENCE_RE.search(raw_response)
    if m:
        return CodeExtractionResult(
            extracted_code=m.group(1).rstrip(),
            extraction_status="success",
        )

    return CodeExtractionResult(
        extracted_code=None,
        extraction_status="no_code_block",
    )
