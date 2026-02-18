from fastapi import APIRouter

from app.api.routes import auth, projects

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(projects.router)
