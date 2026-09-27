from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router

app = FastAPI(title="AI Governance Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten to your real frontend origin once it's hosted somewhere fixed
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")