from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.redis import connect_redis, disconnect_redis
from app.routers import (
    auth,
    workspaces,
    api_keys,
    agents,
    context,
    subscriptions,
    graph,
    directory,
    health,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_redis()
    yield
    await disconnect_redis()


app = FastAPI(
    title=settings.app_name,
    description="The shared context and memory bus for multi-agent AI systems. Build agents, publish context, and watch your AI ecosystem come alive.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(api_keys.router)
app.include_router(agents.router)
app.include_router(context.router)
app.include_router(subscriptions.router)
app.include_router(graph.router)
app.include_router(directory.router)


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "description": "Shared context and memory bus for multi-agent AI systems"
    }