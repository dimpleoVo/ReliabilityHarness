# app/tools/code_executor.py

from reliability_harness.core.engine import ELE_Service


class CodeExecutionTool:
    
    # def __init__(self, use_mock: bool = True):
    #     self.use_mock = use_mock
    def __init__(self):
        self.use_mock = False
        self.service = ELE_Service()

    def run(self, code: str):
        if self.use_mock:
            print("[Mock Execute]:", code)
            return {
                "mode": "mock",
                "result": "mock_result",
                "error": None
            }

        result = self.service.run(code)
        return {
            "mode": "real",
            "result": result,
            "error": None
        }