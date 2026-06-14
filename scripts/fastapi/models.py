from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    """SQLAlchemy model for a user.

    Attributes:
        __tablename__ (str): The name of the database table.
        id (Mapped[int]): The primary key ID of the user.
        username (Mapped[str]): The username of the user.
        email (Mapped[str]): The email address of the user.
        image_file (Mapped[str | None]): The profile image file path of the user.
        posts (Mapped[list[Post]]): The list of posts authored by the user.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    image_file: Mapped[str | None] = mapped_column(
        String(200), nullable=True, default=None
    )

    posts: Mapped[list[Post]] = relationship(
        "Post", back_populates="author", cascade="all, delete-orphan"
    )  # 1 to many relationship

    @property
    def image_path(self) -> str:
        """Get the full path to the user's profile image.

        Returns:
            str: The full path to the profile image.
        """
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"


class Post(Base):
    """SQLAlchemy model for a post.

    Attributes:
        __tablename__ (str): The name of the database table.
        id (Mapped[int]): The primary key ID of the post.
        title (Mapped[str]): The title of the post.
        content (Mapped[str]): The content of the post.
        date_posted (Mapped[datetime]): The date and time the post was created.
        user_id (Mapped[int]): The foreign key ID of the user who authored the post.
        author (Mapped[User]): The relationship to the User model.
    """

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    date_posted: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    author: Mapped[User] = relationship(
        "User", back_populates="posts"
    )  # many to 1 relationship
