from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.movies.models import Movie, Genre


async def get_movie_or_404(movie_id: int, db: AsyncSession) -> Movie:
    stmt = select(Movie).options(selectinload(Movie.genres)).where(Movie.id == movie_id)

    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    return movie


async def get_or_create_genres(
    db: AsyncSession,
    genre_names: list[str],
) -> list[Genre]:
    genres = []

    for genre_name in genre_names:
        stmt = select(Genre).where(Genre.name == genre_name)
        result = await db.execute(stmt)
        genre = result.scalars().first()

        if not genre:
            genre = Genre(name=genre_name)
            db.add(genre)
            await db.flush()

        genres.append(genre)

    return genres
