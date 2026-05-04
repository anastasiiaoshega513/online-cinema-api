from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class GenreSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    year: int
    time: int
    price: float


class MovieListItemSchema(MovieBaseSchema):
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
    description: str
    rating: float
    genres: List[GenreSchema]


class MovieCreateSchema(MovieBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    year: int
    description: str
    rating: float
    genres: List[str]


class MovieUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    name: str | None = None
    time: int | None = None
    price: float | None = None
    year: int | None = None
    description: str | None = None
    rating: float | None = None
