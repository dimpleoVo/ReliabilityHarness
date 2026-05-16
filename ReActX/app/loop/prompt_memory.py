from typing import List, Dict


class MemoryPromptBuilder:
    def build(self, memories: List[Dict]) -> str:
        if not memories:
            return ""

        lines = []
        lines.append("Past failure-fix examples:\n")

        for i, m in enumerate(memories, start=1):
            lines.append(f"[Example {i}]")
            lines.append(f"Task: {m.get('task', '')}")
            lines.append(f"Error Type: {m.get('error_type', '')}")
            lines.append(f"Bad Code:\n{m.get('bad_code', '')}")
            lines.append(f"Bad Output: {m.get('bad_output', '')}")
            if m.get("bad_stderr"):
                lines.append(f"Bad Error:\n{m.get('bad_stderr', '')}")
            lines.append(f"Fixed Code:\n{m.get('fixed_code', '')}")
            lines.append(f"Fixed Output: {m.get('fixed_output', '')}")
            lines.append("")

        lines.append("Use these examples to avoid repeating similar mistakes.\n")
        return "\n".join(lines)