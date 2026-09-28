from fastapi import APIRouter

from app.api.v1 import registration, publication

api_router = APIRouter()
api_router.include_router(registration.router)
api_router.include_router(publication.router)