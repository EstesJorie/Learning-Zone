# scripts/fastapi/schemas.py

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class UserBase(BaseModel):
    """Base model for a user"""

    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    """Model for responding with a user."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    image_file: str | None
    image_path: str


class PostBase(BaseModel):
    """Base model for a post."""

    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)


class PostCreate(PostBase):
    """Model for creating a new post."""

    user_id: int  # temp


class PostResponse(PostBase):
    """Model for responding with a post."""

    model_config = ConfigDict(
        from_attributes=True
    )  # we can read data from attributes of an object, not just dicts

    id: int  # scoped to class, typically we avoid id in Python
    user_id: int
    date_posted: datetime
    author: UserResponse
