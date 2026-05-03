from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class MovieBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    time: str
    price: float


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int


class MovieListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieDetailSchema(MovieBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    year: str
    description: str
    rating: float
    genres: List[str]


class MovieCreateSchema(MovieDetailSchema):
    model_config = ConfigDict(from_attributes=True)
    pass


class MovieUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    name: str | None = None
    time: str | None = None
    price: float | None = None
    year: str | None = None
    description: str | None = None
    rating: float | None = None
    genres: List[str] | None = None

