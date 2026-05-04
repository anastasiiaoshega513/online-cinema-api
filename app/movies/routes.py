from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.dependencies import get_db
from app.movies.models import Movie
from app.movies.schemas import MovieListResponseSchema, MovieListItemSchema, MovieDetailSchema, MovieCreateSchema, MovieUpdateSchema
from app.movies.services import get_movie_or_404, get_or_create_genres

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movie_list(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:

    offset = (page - 1) * per_page
    count_stmt = select(func.count(Movie.id))
    result_count = await db.execute(count_stmt)
    total_items = result_count.scalar() or 0

    stmt = select(Movie).order_by(Movie.id).offset(offset).limit(per_page)

    result_movies = await db.execute(stmt)
    movies = result_movies.scalars().all()

    if not total_items or not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    movie_list = [MovieListItemSchema.model_validate(movie) for movie in movies]

    total_pages = (total_items + per_page - 1) // per_page

    response = MovieListResponseSchema(
        movies=movie_list,
        prev_page=f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        next_page=f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_items,
    )
    return response


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)) -> MovieDetailSchema:

    movie = await get_movie_or_404(movie_id, db)
    return MovieDetailSchema.model_validate(movie)


@router.post("/movies/", response_model=MovieDetailSchema)
async def create_movie(movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)) -> MovieDetailSchema:
    existing_result = await db.execute(
        select(Movie).where(
            (Movie.name == movie_data.name),
            (Movie.year == movie_data.year),
            (Movie.time == movie_data.time)
        )
    )
    existing_movie = existing_result.scalars().first()

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}',"
                f" year {movie_data.year}, time '{movie_data.time}' already exists."
            )
        )
    try:
        genres = await get_or_create_genres(db, movie_data.genres)

        movie = Movie(**movie_data.model_dump(exclude={"genres"}))
        movie.genres = genres
        db.add(movie)
        await db.commit()
        stmt = (
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(Movie.id == movie.id)
        )

        result = await db.execute(stmt)
        created_movie = result.scalar_one()
        return created_movie

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.patch("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def update_movie(movie_id: int, movie_data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)) -> MovieDetailSchema:

    movie = await get_movie_or_404(movie_id, db)

    for field, value in movie_data.model_dump(exclude_unset=True, exclude={"genres"}).items():
        setattr(movie, field, value)

    try:
        await db.commit()
        stmt = (
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(Movie.id == movie.id)
        )

        result = await db.execute(stmt)
        created_movie = result.scalar_one()
        return created_movie
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.delete("/movies/{movie_id}/")
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_or_404(movie_id, db)

    await db.delete(movie)
    await db.commit()
    return {"detail": "Movie deleted successfully."}
