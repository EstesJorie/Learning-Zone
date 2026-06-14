import os
from datetime import datetime  # noqa: F401
from typing import Annotated

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, status, Depends, Response
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from schemas import (
    PostCreate,
    PostResponse,
    UserCreate,
    UserResponse,
    PostUpdate,
    UserUpdate,
)
import models
from database import Base, engine, get_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Async context manager

    Args:
        _app (FastAPI) : An instance of the FastAPI application.
    """
    async with engine.begin() as conn:  # get an async connection
        await conn.run_sync(
            Base.metadata.create_all
        )  # run sync create call in async context
    try:
        yield
    finally:
        await engine.dispose()  # runs at shutdown


app = FastAPI(lifespan=lifespan)  # create instance of FastAPI

templates = Jinja2Templates(directory="templates")  # set up templates
if templates is None:
    raise ValueError(
        "Templates directory not found. Please ensure the 'templates' folder exists."
    )

static_dir = "static"
if not os.path.isdir(static_dir):
    try:
        os.makedirs(static_dir)
    except Exception as e:
        raise ValueError(
            f"Failed to create static directory '{static_dir}'. Please ensure the application has the necessary permissions. Error: {e}"
        )

app.mount("/static", StaticFiles(directory=static_dir), name="static")

media_dir = "media"
if not os.path.isdir(media_dir):
    try:
        os.makedirs(media_dir)
    except Exception as e:
        raise ValueError(
            f"Failed to create media directory '{media_dir}'. Please ensure the application has the necessary permissions. Error: {e}"
        )
app.mount("/media", StaticFiles(directory=media_dir), name="media")

# ------- ENDPOINTS -------


@app.get(
    "/", include_in_schema=False, name="home"
)  # define a route for the root endpoint
@app.get(
    "/posts", include_in_schema=False, name="posts"
)  # stack routes to the same function
async def home(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)]
):  # define the function to handle the request
    """Render the home page with a list of posts.

    Args:
        request (Request): The incoming request.
        db (Session): A database session.

    Returns:
        TemplateResponse: The rendered home page.
    """
    res = await db.execute(
        select(models.Post).options(selectinload(models.Post.author))
    )
    posts = res.scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "posts": posts,
            "title": "Home",
        },
    )  # render the template with the posts data


@app.get("/posts/{post_id}", include_in_schema=False, name="post_page")
async def post_page(
    request: Request, post_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):
    """Render a specific post page based on the post ID.

    Args:
        request (Request): The incoming request.
        post_id (int): The ID of the post to retrieve.
        db (Session): A database session.

    Returns:
        TemplateResponse: The rendered post page.
    """
    res = await db.execute(
        select(models.Post)
        .options(
            selectinload(models.Post.author)
        )  # pass eager load before WHERE clause
        .where(models.Post.id == post_id)
    )
    post = res.scalars().first()
    if post:
        title = post.title[:50]
        return templates.TemplateResponse(
            request,
            "post.html",
            {"post": post, "title": title},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@app.get(
    "/users/{user_id}/posts",
    include_in_schema=False,
    name="user_posts_page",
)
async def user_posts_page(
    request: Request, user_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):
    """Render a page showing posts for a specific user.

    This is the HTML page counterpart to the API `user_posts` endpoint.
    """
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
    )
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {
            "user": user,
            "posts": posts,
            "title": f"Posts by {user.username}",
        },
    )


@app.get("/api/posts", response_model=list[PostResponse])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    """Retrieve all posts from the database.

    Args:
        db (Session): A database session.
    Returns:
        List[PostResponse]: List of all posts.
    """
    result = await db.execute(
        select(models.Post).options(selectinload(models.Post.author))
    )
    posts = result.scalars().all()
    return posts


@app.get(
    "/api/posts/{post_id}",
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


@app.get(
    "/api/users/{user_id}/posts",
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


@app.post(
    "/api/posts",
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


@app.post(
    path="/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
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


@app.get("/api/users/{user_id}", response_model=UserResponse)
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


@app.put(path="/api/posts/{post_id}", response_model=PostResponse)
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


@app.patch(path="/api/posts/{post_id}", response_model=PostResponse)
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


@app.patch(path="/api/users/{user_id}", response_model=UserResponse)
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


@app.delete(
    "/api/posts/{post_id}",
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
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.delete(path="/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
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


# ------- EXCEPTIONS -------


@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle general HTTP exceptions for both API and web routes.

    Args:
        request (Request): The incoming request.
        exc (StarletteHTTPException): The HTTP exception.

    Returns:
        JSONResponse or TemplateResponse: Returns a JSON response for API routes and a template response for
        web routes.
    """
    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exc)

    message = (
        exc.detail
        if exc.detail
        else "An unexpected error occurred. Please try check your request and try again."
    )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exc.status_code,
            "title": exc.status_code,
            "message": message,
        },
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors for both API and web routes.

    Args:
        request (Request): The incoming request.
        exc (RequestValidationError): The validation error exception.

    Returns:
        JSONResponse or TemplateResponse: Returns a JSON response for API routes and a template response for
        web routes.
    """
    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request, exc)
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "title": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "message": "Validation error. Please check your request and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
