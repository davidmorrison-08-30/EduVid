from fastapi import BackgroundTasks, FastAPI, HTTPException
from .app.jobs import create_job, get_job, run_job
from .app.schemas import GenerateRequest, GenerateResponse, JobStatus

app = FastAPI(title="Chemistry Concept Video Generator", version="1.0.0")

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest, background_tasks: BackgroundTasks)-> GenerateResponse:
    job = create_job(request.concept)
    background_tasks.add_task(run_job, job.job_id)

    return GenerateResponse(job_id=job.job_id, state=job.state)

@app.get("/status/{job_id}", response_model=JobStatus)
def status(job_id: str) -> JobStatus:
    """Return the current job status, including the saved video path when done."""
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/ping")
async def ping():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8088)