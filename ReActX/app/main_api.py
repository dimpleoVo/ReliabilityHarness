from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Body
from pydantic import BaseModel

from app.loop.closed_loop_runner import run_closed_loop

print("MAIN START")
app = FastAPI(title="ReActX API", version="2.0")


class QueryRequest(BaseModel):
    query: Optional[str] = ""


@app.post("/v1/agent/run")
async def run_agent(
    request: Request,
    body: QueryRequest = Body(default=QueryRequest())
):
    try:
        content_type = request.headers.get("content-type", "")
        query = ""

        if "application/json" in content_type:
            query = (body.query or "").strip()
        else:
            raw = await request.body()
            query = raw.decode("utf-8").strip()

        if not query:
            raise HTTPException(status_code=400, detail="Empty query")

        result = run_closed_loop(query)
        return {"status": "success", "result": result}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    return {"status": "healthy"}