# =============================================================
# amenity.py - Pydantic schemas for the Amenity entity
# =============================================================

from pydantic import BaseModel, ConfigDict, Field


class AmenityResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class AmenityCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
