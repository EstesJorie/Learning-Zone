from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Annotated

import models
from database import get_db
from schemas import PostResponse, PostCreate, PostUpdate

router = APIRouter()


@router.get("", response_model=list[PostResponse])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    """Retrieve all posts from the database.

    Args:
        db (Session): A database session.
    Returns:
        List[PostResponse]: List of all posts.
    """
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .order_by(models.Post.date_posted.desc())  # order by newest fiorst
    )
    posts = result.scalars().all()
    return posts


@router.get(
    "/{post_id}",
    response_model=PostResponse,
)
async def get_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    """Retrieve a specific post by ID.

    Args:
        post_id (int): The ID of the post.
        db (Session): A database session.

    Returns:
        PostResponse: The requested post.
    """
    res = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id)
    )
    post = res.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(post: PostCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    """Create a new post.

    Args:
        post (PostCreate): The post data to create.
        db (Session): A database session.

    Returns:
            PostResponse: The created post.
    """
    result = await db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id,
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(
        new_post, attribute_names=["author"]
    )  # we need author to be loaded for post response
    return new_post


@router.put(path="/{post_id}", response_model=PostResponse)
async def update_post_full(
    post_id: int, post_data: PostCreate, db: Annotated[AsyncSession, Depends(get_db)]
):
    """Update a post via PUT

    Args:
        post_id (int): The ID of the post.
        post_data (PostCreate): The post data to update.
        db (Session): A database session.

    Returns:
        PostResponse: The updated post.

    Raises:
        HTTPException: If the post does not exist.
    """
    res = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = res.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if post_data.user_id != post.user_id:
        res = await db.execute(
            select(models.User).where(models.User.id == post_data.user_id)
        )
        usr = res.scalars().first()
        if not usr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

    post.title = post_data.title
    post.content = post_data.content
    post.user_id = post_data.user_id

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post


@router.patch(path="/{post_id}", response_model=PostResponse)
async def update_post_partial(
    post_id: int, post_data: PostUpdate, db: Annotated[AsyncSession, Depends(get_db)]
):
    """Update a post via PATCH

    Args:
        post_id (int): The ID of the post.
        post_data (PostCreate): The post data to update.
        db (Session): A database session.

    Returns:
        PostResponse: The updated post.

    Raises:
        HTTPException: If the post does not exist.
    """
    res = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = res.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    update_data = post_data.model_dump(exclude_unset=True)  # contains data from body
    for field, value in update_data.items():
        """Dynamically set attributes for each changed field"""
        setattr(
            post, field, value
        )  # set the post attributes with the field (ie TITLE) with new value

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,  # return 204 no content as it has been deleted
)
async def delete_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    """Delete a specific post by ID.

    Args:
        post_id (int): The ID of the post.
        db (Session): A database session.

    Returns:
       204 NO CONTENT: Delete is successful and returns no content
    """
    res = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = res.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    await db.delete(post)
    await db.commit()
