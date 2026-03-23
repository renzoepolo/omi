from fastapi import APIRouter

from app.api.routes import admin, auth, observations, projects

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(observations.router)
api_router.include_router(admin.router)
