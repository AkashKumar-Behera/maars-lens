from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models import Area, OfficerAreaAssignment, Profile as UserProfile

router = APIRouter(prefix="/areas", tags=["areas"])

@router.get("/")
async def list_areas(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    result = await db.execute(select(Area))
    return result.scalars().all()
