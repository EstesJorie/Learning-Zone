import os
from datetime import datetime  # noqa: F401
from typing import Annotated

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas import PostCreate, PostResponse, UserCreate, UserResponse
import models
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)  # creates table if not exists, IDEMPOTENT

app = FastAPI()  # create instance of FastAPI

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
def home(
    request: Request, db: Annotated[Session, Depends(get_db)]
):  # define the function to handle the request
    """Render the home page with a list of posts.

    Args:
        request (Request): The incoming request.
        db (Session): A database session.

    Returns:
        TemplateResponse: The rendered home page.
    """
    res = db.execute(select(models.Post))
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
def post_page(request: Request, post_id: int, db: Annotated[Session, Depends(get_db)]):
    """Render a specific post page based on the post ID.

    Args:
        request (Request): The incoming request.
        post_id (int): The ID of the post to retrieve.
        db (Session): A database session.

    Returns:
        TemplateResponse: The rendered post page.
    """
    res = db.execute(select(models.Post).where(models.Post.id == post_id))
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
def user_posts_page(
    request: Request, user_id: int, db: Annotated[Session, Depends(get_db)]
):
    """Render a page showing posts for a specific user.

    This is the HTML page counterpart to the API `user_posts` endpoint.
    """
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
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
def get_posts(db: Annotated[Session, Depends(get_db)]):
    """Retrieve all posts from the database.

    Args:
        db (Session): A database session.
    Returns:
        List[PostResponse]: List of all posts.
    """
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts


@app.get(
    "/api/posts/{post_id}",
    response_model=PostResponse,
)
def get_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    """Retrieve a specific post by ID.

    Args:
        post_id (int): The ID of the post.
        db (Session): A database session.

    Returns:
        PostResponse: The requested post.
    """
    res = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = res.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@app.get(
    "/api/users/{user_id}/posts",
    response_model=list[PostResponse],
    name="user_posts",
)
def get_user_posts(user_id: int, db: Annotated[Session, Depends(get_db)]):
    """Retrieve all posts for a specific user by user ID.

    Args:
        user_id (int): The ID of the user.
        db (Session): A database session.

    Returns:
        List[PostResponse]: List of posts for the specified user.
    """
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return posts


@app.post(
    "/api/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(post: PostCreate, db: Annotated[Session, Depends(get_db)]):
    """Create a new post.

    Args:
        post (PostCreate): The post data to create.
        db (Session): A database session.

    Returns:
            PostResponse: The created post.
    """
    result = db.execute(select(models.User).where(models.User.id == post.user_id))
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
    db.commit()
    db.refresh(new_post)
    return new_post


@app.post(
    path="/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    """Create a new user.

    Args:
        user (UserCreate): The user data to create.
        db (Session): A database session.

    Returns:
        UserResponse: The created user.

    Raises:
        HTTPException: If the username or email already exists.
    """

    result = db.execute(
        select(models.User).where(models.User.username == user.username)
    )
    existing_user = result.scalars().first()  # gets first User obj or None if no match

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )

    result = db.execute(select(models.User).where(models.User.email == user.email))
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
    db.commit()  # executes insert
    db.refresh(new_user)  # reloads obj from db

    return new_user


@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    """Get a user by ID.

    Args:
        user_id (int): The ID of the user.
        db (Session): A database session.

    Returns:
        UserResponse: The requested user.
    """
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()  # gets first User obj or None if no match

    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


# ------- EXCEPTIONS -------


@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle general HTTP exceptions for both API and web routes.

    Args:
        request (Request): The incoming request.
        exc (StarletteHTTPException): The HTTP exception.

    Returns:
        JSONResponse or TemplateResponse: Returns a JSON response for API routes and a template response for
        web routes.
    """
    message = (
        exc.detail
        if exc.detail
        else "An unexpected error occurred. Please try check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": message},
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
def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors for both API and web routes.

    Args:
        request (Request): The incoming request.
        exc (RequestValidationError): The validation error exception.

    Returns:
        JSONResponse or TemplateResponse: Returns a JSON response for API routes and a template response for
        web routes.
    """
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )
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
