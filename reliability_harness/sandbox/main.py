from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from reliability_harness.sandbox.executor import DockerSandboxExecutor

app = FastAPI(title="ReActX Sandbox Service", version="1.0.0")
executor = DockerSandboxExecutor()


class ExecuteRequest(BaseModel):
    code: str = Field(..., description="Python code to execute")
    timeout: int = Field(default=10, ge=1, le=60)
    image: str = Field(default="python:3.11-slim")


class ExecuteResponse(BaseModel):
    status: str
    stdout: str
    stderr: str
    return_code: int
    timeout: bool
    runtime_error: bool
    runtime: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/execute", response_model=ExecuteResponse)
def execute(req: ExecuteRequest):
    try:
        result = executor.run_python(
            code=req.code,
            timeout=req.timeout,
            image=req.image,
        )
        return ExecuteResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))