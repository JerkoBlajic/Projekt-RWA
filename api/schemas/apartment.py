# =============================================================
# apartment.py - Pydantic schemas for the Apartment entity
# =============================================================
# Validation rules (section 13 of the spec):
#   price_per_night > 0, max_guests > 0, bedrooms >= 0, bathrooms >= 0
# =============================================================

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.amenity import AmenityResponse
from schemas.user import UserResponse

# An image is either a URL or a base64 data URI uploaded from the browser.
# ~3 MB of characters ~= a ~2 MB binary image after base64 - plenty for a
# client-downscaled photo, small enough to keep DB rows sane.
MAX_IMAGE_LEN = 3_000_000


def _clean_image(cls, v: str | None) -> str | None:  # noqa: N805
    if v is None:
        return None
    v = v.strip()
    if not v:
        return None
    if len(v) > MAX_IMAGE_LEN:
        raise ValueError("image is too large; upload a smaller picture")
    if not v.startswith(("http://", "https://", "data:image/")):
        raise ValueError("image must be a URL or an uploaded image")
    return v


class ApartmentBase(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    image: str | None = Field(default=None)
    _v_image = field_validator("image")(classmethod(_clean_image))
    description: str = Field(default="", max_length=5000)
    address: str = Field(min_length=3, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    price_per_night: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    max_guests: int = Field(gt=0, le=100)
    bedrooms: int = Field(ge=0, le=50)
    bathrooms: int = Field(ge=0, le=50)
    area_sqm: int | None = Field(default=None, gt=0, le=10000)


class ApartmentCreate(ApartmentBase):
    amenity_ids: list[int] = Field(default_factory=list)


class ApartmentUpdate(BaseModel):
    """All fields optional - only the provided ones are changed."""

    title: str | None = Field(default=None, min_length=3, max_length=150)
    image: str | None = Field(default=None)
    description: str | None = Field(default=None, max_length=5000)
    _v_image = field_validator("image")(classmethod(_clean_image))
    address: str | None = Field(default=None, min_length=3, max_length=255)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    price_per_night: Decimal | None = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )
    max_guests: int | None = Field(default=None, gt=0, le=100)
    bedrooms: int | None = Field(default=None, ge=0, le=50)
    bathrooms: int | None = Field(default=None, ge=0, le=50)
    area_sqm: int | None = Field(default=None, gt=0, le=10000)
    amenity_ids: list[int] | None = None


class OwnerBrief(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class ApartmentResponse(BaseModel):
    id: int
    owner_id: int
    title: str
    image: str | None
    description: str
    address: str
    city: str
    price_per_night: Decimal
    max_guests: int
    bedrooms: int
    bathrooms: int
    area_sqm: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    amenities: list[AmenityResponse] = []
    owner: OwnerBrief | None = None

    model_config = ConfigDict(from_attributes=True)
