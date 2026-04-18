from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.redis import connect_redis, disconnect_redis
from app.routers import agents, context, subscriptions, graph, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_redis()
    yield
    await disconnect_redis()


app = FastAPI(
    title=settings.app_name,
    description="Shared context and memory bus for multi-agent AI systems",
    version="0.1.0",
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
app.include_router(agents.router)
app.include_router(context.router)
app.include_router(subscriptions.router)
app.include_router(graph.router)


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }