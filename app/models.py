from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)

    @field_validator("username")
    @classmethod
    def username_must_be_alphanumeric(cls, v: str) -> str:
        if not all(c.isalnum() or c == "_" for c in v):
            raise ValueError("Username deve conter apenas letras, números e underscores")
        return v.lower()


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    genres: str = Field(default="Unknown", max_length=500)


class ItemResponse(BaseModel):
    id: int
    title: str
    genres: str

    model_config = {"from_attributes": True}


class RatingCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    item_id: int = Field(..., gt=0)
    rating: float = Field(..., ge=0.5, le=5.0)

    @field_validator("rating")
    @classmethod
    def rating_must_be_half_step(cls, v: float) -> float:
        if round(v * 2) != v * 2:
            raise ValueError("A nota deve ser um múltiplo de 0.5")
        return round(v, 1)


class RatingResponse(BaseModel):
    id: int
    user_id: int
    item_id: int
    rating: float
    timestamp: datetime

    model_config = {"from_attributes": True}


class RecommendationResponse(BaseModel):
    item_id: int
    title: str
    predicted_rating: float
    genres: str


class RecommendationList(BaseModel):
    user_id: int
    recommendations: List[RecommendationResponse]
    total: int


class RatingHistory(BaseModel):
    user_id: int
    username: str
    ratings: List[RatingResponse]
    total: int
