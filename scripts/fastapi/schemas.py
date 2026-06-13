# scripts/fastapi/schemas.py

from pydantic import BaseModel, ConfigDict, Field


class PostBase(BaseModel):
    """Base model for a post."""

    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=50)


class PostCreate(PostBase):
    """Model for creating a new post."""

    pass


class PostResponse(PostBase):
    """Model for responding with a post."""

    model_config = ConfigDict(
        from_attributes=True
    )  # we can read data from attributes of an object, not just dicts

    id: int  # scoped to class, typically we avoid id in Python
    date_posted: str
