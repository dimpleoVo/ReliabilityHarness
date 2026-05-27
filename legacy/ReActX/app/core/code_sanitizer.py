import re


import re


class CodeSanitizer:

    @staticmethod
    def extract_code(text: str) -> str:
        if not text:
            return ""

        # 🔥 关键：允许 python 后有换行 / 空格
        match = re.search(r"```python\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # fallback：任意代码块
        match = re.search(r"```\s*(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()

        return ""

    @staticmethod
    def looks_like_code(line: str) -> bool:
        s = line.strip()
        if not s:
            return False

        code_prefixes = (
            "print(",
            "def ",
            "for ",
            "while ",
            "if ",
            "elif ",
            "else:",
            "import ",
            "from ",
            "return ",
            "class ",
            "try:",
            "except",
            "with ",
        )

        if s.startswith(code_prefixes):
            return True

        if "=" in s:
            return True

        # 纯英文/数字/符号的简单表达式也允许
        if re.fullmatch(r"[A-Za-z0-9_ \(\)\[\]\{\}\+\-\*/%,\.:\"'`]+", s):
            return True

        return False

    @staticmethod
    def filter_code_lines(text: str) -> str:
        lines = text.splitlines()
        kept = [line for line in lines if CodeSanitizer.looks_like_code(line)]
        return "\n".join(kept).strip()

    @staticmethod
    def ensure_print(code: str) -> str:
        if not code:
            return ""

        if "print(" in code:
            return code

        lines = [line for line in code.strip().split("\n") if line.strip()]
        if not lines:
            return ""

        last = lines[-1].strip()

        # 只在最后一行看起来像合法表达式时补 print
        if re.fullmatch(r"[A-Za-z0-9_ \(\)\[\]\{\}\+\-\*/%,\.:\"']+", last) and not last.startswith(
            ("def ", "for ", "while ", "if ", "elif ", "else", "import ", "from ", "class ")
        ):
            return code + f"\nprint({last})"

        return code

    @staticmethod
    def sanitize(raw_output: str) -> str:
        code = CodeSanitizer.extract_code(raw_output)
        code = CodeSanitizer.filter_code_lines(code)
        code = CodeSanitizer.ensure_print(code)
        return code.strip()