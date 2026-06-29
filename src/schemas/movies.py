from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class MovieStatusEnum(str, Enum):
    released = "Released"
    post_production = "Post Production"
    in_production = "In Production"


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    model_config = {"from_attributes": True}


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: Optional[CountrySchema] = None
    genres: list[GenreSchema] = []
    actors: list[ActorSchema] = []
    languages: list[LanguageSchema] = []

    model_config = {"from_attributes": True}


class MovieCreateSchema(BaseModel):
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: str
    genres: list[str] = []
    actors: list[str] = []
    languages: list[str] = []

    @field_validator("name")
    @classmethod
    def name_max_length(cls, v: str) -> str:
        if len(v) > 255:
            raise ValueError("Name must not exceed 255 characters.")
        return v

    @field_validator("date")
    @classmethod
    def date_not_too_far(cls, v: date) -> date:
        if v > date.today() + timedelta(days=365):
            raise ValueError("Date must not be more than one year in the future.")
        return v

    @field_validator("score")
    @classmethod
    def score_range(cls, v: float) -> float:
        if not (0 <= v <= 100):
            raise ValueError("Score must be between 0 and 100.")
        return v

    @field_validator("budget", "revenue")
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Must be non-negative.")
        return v


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    @field_validator("score")
    @classmethod
    def score_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("Score must be between 0 and 100.")
        return v

    @field_validator("budget", "revenue")
    @classmethod
    def non_negative(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Must be non-negative.")
        return v