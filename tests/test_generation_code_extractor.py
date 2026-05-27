"""
Tests for reliability_harness.runtime.generation.code_extractor.

No LLM calls. No Docker. No .env reading. No output writes.
"""
import pytest

from reliability_harness.runtime.generation.code_extractor import (
    CodeExtractionResult,
    extract_python_code,
)


class TestExtractPythonCode:
    def test_python_fenced_block_success(self):
        raw = "Here is the solution:\n```python\ndef add(a, b):\n    return a + b\n```"
        result = extract_python_code(raw)
        assert result.extraction_status == "success"
        assert result.extracted_code is not None
        assert "def add(a, b):" in result.extracted_code

    def test_generic_fenced_block_success(self):
        raw = "Solution:\n```\ndef add(a, b):\n    return a + b\n```"
        result = extract_python_code(raw)
        assert result.extraction_status == "success"
        assert result.extracted_code is not None
        assert "def add(a, b):" in result.extracted_code

    def test_no_code_block_returns_no_code_block(self):
        raw = "Here is the solution: def add(a, b): return a+b"
        result = extract_python_code(raw)
        assert result.extraction_status == "no_code_block"
        assert result.extracted_code is None

    def test_empty_string_returns_empty_response(self):
        result = extract_python_code("")
        assert result.extraction_status == "empty_response"
        assert result.extracted_code is None

    def test_whitespace_only_returns_empty_response(self):
        result = extract_python_code("   \n  \t  ")
        assert result.extraction_status == "empty_response"
        assert result.extracted_code is None

    def test_returns_code_extraction_result_instance(self):
        result = extract_python_code("```python\nprint('hello')\n```")
        assert isinstance(result, CodeExtractionResult)

    def test_python_fence_preferred_over_generic(self):
        raw = "```\ngeneric code\n```\n\n```python\ndef specific(): pass\n```"
        result = extract_python_code(raw)
        assert result.extraction_status == "success"
        assert "specific" in result.extracted_code

    def test_multiline_code_extracted(self):
        raw = "```python\ndef solve(n):\n    total = 0\n    for i in range(n):\n        total += i\n    return total\n```"
        result = extract_python_code(raw)
        assert result.extraction_status == "success"
        assert "def solve(n):" in result.extracted_code
        assert "return total" in result.extracted_code

    def test_no_code_block_error_field_is_none(self):
        result = extract_python_code("no fence here")
        assert result.error is None

    def test_success_error_field_is_none(self):
        result = extract_python_code("```python\ndef f(): pass\n```")
        assert result.error is None

    def test_extraction_does_not_add_print(self):
        raw = "```python\ndef add(a, b):\n    return a + b\n```"
        result = extract_python_code(raw)
        assert "print(" not in result.extracted_code
