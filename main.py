from app.graph import workflow
from typing import Dict, Any, Optional
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from fastapi import FastAPI
from app.schemas import GenerateRequest, GenerateResponse

app = FastAPI(title="Chemistry Concept Video Generator", version="1.0.0")

@app.post("/generate")
async def generate(request: GenerateRequest):
    # Extract prompt and session ID from AgentCore request context
    concept = request.concept
    # session_id = getattr(context, "session_id", "default-session")

    # config = {"configurable": {"thread_id": session_id}}
    initial_state = {
        "job_id": "",
        "concept": concept,
        "codegen_iterations": 0,
        "alignment_iterations": 0,
    }
    result = await workflow.ainvoke(
        initial_state
    )

    return {"output_dir": result.get("video_path")}

@app.get("/ping")
async def ping():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8088)