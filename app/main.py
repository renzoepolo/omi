from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)

PROJECT_ID_EXEMPT_PATHS = {
    "/auth/login",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/health",
    "/projects",
    "/projects/",
}


@app.middleware("http")
async def require_project_id(request: Request, call_next):
    if request.url.path not in PROJECT_ID_EXEMPT_PATHS:
        project_id = request.headers.get("X-Project-Id")
        if not project_id:
            return JSONResponse(status_code=400, content={"detail": "Missing X-Project-Id header"})
        if not project_id.isdigit():
            return JSONResponse(status_code=400, content={"detail": "X-Project-Id must be numeric"})
        request.state.active_project_id = int(project_id)

    return await call_next(request)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(api_router)
