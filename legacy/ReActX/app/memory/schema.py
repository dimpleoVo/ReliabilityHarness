from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class FailureMemoryItem:
    task: str
    task_type: str
    error_type: str
    bad_code: str
    bad_output: str
    bad_stderr: str
    fixed_code: str
    fixed_output: str
    improved: bool
    meta: Optional[Dict[str, Any]] = None
    bad_step: Optional[Dict[str, Any]] = None
    fixed_step: Optional[Dict[str, Any]] = None


    def to_dict(self):
        return asdict(self)