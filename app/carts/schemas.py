from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict

from movies.schemas import MovieBaseSchema


class CartItemScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie: MovieBaseSchema
    added_at: datetime


class CartResponseScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    detail: str = "There are your movies, thank you for your choice!"
    items: List[CartItemScheme] | None = None
