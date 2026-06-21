import os
from datetime import datetime  # noqa: F401
from typing import Annotated

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, status, Depends
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

import models
from database import Base, engine, get_db
from routers import posts, users


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

app.include_router(
    router=users.router, prefix="/api/users", tags=["users"], deprecated=False
)
app.include_router(
    router=posts.router, prefix="/api/posts", tags=["posts"], deprecated=False
)

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
        select(models.Post)
        .options(selectinload(models.Post.author))
        .order_by(models.Post.date_posted.desc())  # order by newest first
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
        .order_by(models.Post.date_posted.desc())  # order by newest first
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
