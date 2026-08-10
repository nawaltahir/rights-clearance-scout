"""
FastAPI backend for the Rights & Clearance Scout demo.

Serves a single-page upload UI (static/index.html) and one endpoint that
runs the full extract -> research -> classify pipeline against submitted
script text.
"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent.rights_scout_agent import run_pipeline

app = FastAPI(title="Rights & Clearance Scout")
app.mount("/static", StaticFiles(directory="static"), name="static")


class ScanRequest(BaseModel):
    script_text: str


class ScanResponse(BaseModel):
    report: list[dict]


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.post("/api/scan", response_model=ScanResponse)
def scan(req: ScanRequest):
    """Run the full clearance-risk pipeline on submitted script text."""
    report = run_pipeline(req.script_text)
    return ScanResponse(report=report)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
