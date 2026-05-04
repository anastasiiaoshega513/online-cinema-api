from sqlalchemy import Column, Integer, String, Table, ForeignKey, UniqueConstraint, Text, Float, Numeric
from sqlalchemy.orm import Relationship

from db.engine import Base


MoviesGenresModel = Table(
    "movies_genres",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column(
        "genre_id",
        ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True, nullable=False),
)


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    movies = Relationship(
        "Movie",
        secondary=MoviesGenresModel,
        back_populates="genres",
    )

    def __repr__(self):
        return f"<Genre(name='{self.name}')>"


class Movie(Base):
    __tablename__ = "movies"

    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="unique_movie_constraint"),
    )

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    time = Column(Integer, nullable=False)

    description = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    rating = Column(Float, nullable=True)

    genres = Relationship(
        "Genre",
        secondary=MoviesGenresModel,
        back_populates="movies",
    )
    cart_items = Relationship(
        "CartItem",
        back_populates="movie",
    )

    def __repr__(self):
        return f"<Movie(name='{self.name}', release_year='{self.year}', rating={self.rating})>"
