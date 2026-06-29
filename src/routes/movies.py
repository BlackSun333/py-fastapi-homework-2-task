from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from database.models import (
    MovieModel,
    GenreModel,
    ActorModel,
    CountryModel,
    LanguageModel,
)
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_items_result.scalar()

    total_pages = (total_items + per_page - 1) // per_page

    offset = (page - 1) * per_page
    result = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    base = "/theater/movies/"
    prev_page = f"{base}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        body = await request.json()
        data = MovieCreateSchema(**body)
    except (ValidationError, Exception):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    existing = await db.execute(
        select(MovieModel).where(
            MovieModel.name == data.name,
            MovieModel.date == data.date,
        )
    )
    if existing.scalar():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{data.name}' and release date '{data.date}' already exists.",
        )

    country_result = await db.execute(
        select(CountryModel).where(CountryModel.code == data.country)
    )
    country = country_result.scalar()
    if not country:
        country = CountryModel(code=data.country)
        db.add(country)
        await db.flush()

    genres = []
    for name in data.genres:
        result = await db.execute(select(GenreModel).where(GenreModel.name == name))
        genre = result.scalar()
        if not genre:
            genre = GenreModel(name=name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    actors = []
    for name in data.actors:
        result = await db.execute(select(ActorModel).where(ActorModel.name == name))
        actor = result.scalar()
        if not actor:
            actor = ActorModel(name=name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    # Languages
    languages = []
    for name in data.languages:
        result = await db.execute(select(LanguageModel).where(LanguageModel.name == name))
        lang = result.scalar()
        if not lang:
            lang = LanguageModel(name=name)
            db.add(lang)
            await db.flush()
        languages.append(lang)

    movie = MovieModel(
        name=data.name,
        date=data.date,
        score=data.score,
        overview=data.overview,
        status=data.status,
        budget=data.budget,
        revenue=data.revenue,
        country_id=country.id,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(movie)
    await db.commit()

    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie.id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    return result.scalar()


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    movie = result.scalar()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        body = await request.json()
        data = MovieUpdateSchema(**body)
    except (ValidationError, Exception):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(movie, field, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
