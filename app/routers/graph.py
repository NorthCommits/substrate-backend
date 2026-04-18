from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import graph_service


router = APIRouter(prefix="/graph", tags=["Graph"])


@router.get("/")
async def get_graph(
    db: AsyncSession = Depends(get_db)
):
    return await graph_service.build_graph(db)