# =============================================================
# amenities.py - Amenity endpoints
# =============================================================
#   GET  /amenities            (public)
#   POST /amenities            (admin)   201
# =============================================================

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_db, require_admin
from schemas.amenity import AmenityCreate, AmenityResponse
from services import amenity_service

router = APIRouter()


@router.get("", response_model=list[AmenityResponse])
async def list_amenities(db: AsyncSession = Depends(get_db)):
    return await amenity_service.list_amenities(db)


@router.post(
    "",
    response_model=AmenityResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_amenity(body: AmenityCreate, db: AsyncSession = Depends(get_db)):
    return await amenity_service.create_amenity(db, body)
