from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Annotated

import models
from database import get_db
from schemas import PostResponse, UserCreate, UserResponse, UserUpdate

router = APIRouter()


@router.get(
    "/{user_id}/posts",
    response_model=list[PostResponse],
    name="user_posts",
)
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    """Retrieve all posts for a specific user by user ID.

    Args:
        user_id (int): The ID of the user.
        db (Session): A database session.

    Returns:
        List[PostResponse]: List of posts for the specified user.
    """
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
    )
    posts = result.scalars().all()
    return posts


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    """Get a user by ID.

    Args:
        user_id (int): The ID of the user.
        db (Session): A database session.

    Returns:
        UserResponse: The requested user.
    """
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()  # gets first User obj or None if no match

    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.post(path="", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    """Create a new user.

    Args:
        user (UserCreate): The user data to create.
        db (Session): A database session.

    Returns:
        UserResponse: The created user.

    Raises:
        HTTPException: If the username or email already exists.
    """

    result = await db.execute(
        select(models.User).where(models.User.username == user.username)
    )
    existing_user = result.scalars().first()  # gets first User obj or None if no match

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )

    result = await db.execute(
        select(models.User).where(models.User.email == user.email)
    )
    existing_email = result.scalars().first()  # gets first User obj or None if no match

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
        )

    new_user = models.User(
        username=user.username,
        email=user.email,
    )
    db.add(new_user)  # stages insert
    await db.commit()  # executes insert
    await db.refresh(new_user)  # reloads obj from db

    return new_user


@router.patch(path="/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, user_update: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]
):
    """Update a user via PATCH

    Args:
        user_id (int): The ID of the user.
        user_update (UserUpdate): The user data to update.
        db (Session): A database session.

    Returns:
        UserResponse: The updated user.

    Raises:
        404 HTTPException: If the user does not exist.
        400 HTTPException: If the user/email already exists.
    """
    res = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )  # find user
    usr = res.scalars().first()
    if not usr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user_update.username != usr.username and user_update.username is not None:
        """If new username is supplied, check if username is different and if it already exists"""
        res = await db.execute(
            select(models.User).where(models.User.username == user_update.username)
        )
        existing_usr = res.scalars().first()
        if existing_usr:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

    if user_update.email != usr.email and user_update.email is not None:
        """If new email is supplied, check if email is different and if it already exists"""
        res = await db.execute(
            select(models.User).where(models.User.email == user_update.email)
        )
        existing_email = res.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
            )

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(usr, field, value)

    await db.commit()
    await db.refresh(usr)
    return usr


@router.delete(path="/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    """Delete a specific user by ID.

    Args:
        user_id (int): The ID of the user to be deleted.
        db (Session): A database session.

    Returns:
        204 NO CONTENT: Delete is successful and returns no content
    """
    res = await db.execute(select(models.User).where(models.User.id == user_id))
    user = res.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    await db.delete(user)
    await db.commit()
