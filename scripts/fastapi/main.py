import os
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from schemas import PostCreate, PostResponse

app = FastAPI()  # create instance of FastAPI

templates = Jinja2Templates(directory="templates")  # set up templates
if templates is None:
    raise ValueError(
        "Templates directory not found. Please ensure the 'templates' folder exists."
    )

static_dir = "static"
if not os.path.isdir(static_dir):
    raise ValueError(
        f"Static directory '{static_dir}' not found. Please ensure the 'static' folder exists."
    )

app.mount("/static", StaticFiles(directory=static_dir), name="static")

posts: list[dict] = [
    {
        "id": 1,
        "author": "Joe Bloggs",
        "title": "FastAPI rules!",
        "content": "This was really easy to use and super fast.",
        "date_posted": "June 15, 2026",
    },
    {
        "id": 2,
        "author": "Joe Floggs",
        "title": "Python is great for this",
        "content": "Python is a good choice for web development backends.",
        "date_posted": "June 14, 2026",
    },
]

# ------- ENDPOINTS -------


@app.get(
    "/", include_in_schema=False, name="home"
)  # define a route for the root endpoint
@app.get(
    "/posts", include_in_schema=False, name="posts"
)  # stack routes to the same function
def home(request: Request):  # define the function to handle the request
    """Render the home page with a list of posts.

    Args:
        request (Request): The incoming request.

    Returns:
        TemplateResponse: The rendered home page.
    """
    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "posts": posts,
            "title": "Home",
        },
    )  # render the template with the posts data


@app.get("/posts/{post_id}", include_in_schema=False, name="post_page")
def post_page(request: Request, post_id: int):
    """Render a specific post page based on the post ID.

    Args:
        request (Request): The incoming request.
        post_id (int): The ID of the post to retrieve.

    Returns:
        TemplateResponse: The rendered post page.
    """
    for post in posts:
        if post.get("id") == post_id:
            post_title = post["title"][:50]  # Limit title to 50 characters
            return templates.TemplateResponse(
                request, "post.html", {"post": post, "title": post_title}
            )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@app.get("/api/posts", response_model=list[PostResponse])
def get_posts():
    """Retrieve all posts.

    Returns:
        list[PostResponse]: A list of all posts.
    """
    return posts


@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int):
    """Retrieve a specific post by ID.

    Args:
        post_id (int): The ID of the post to retrieve.

    Returns:
        PostResponse: The requested post.
    """
    for post in posts:
        if post.get("id") == post_id:
            return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@app.post(
    path="/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED
)
def create_post(post: PostCreate):
    """Create a new post.

    Args:
        post (PostCreate): The post data to create.

    Returns:
        PostResponse: The created post.
    """
    new_id = max(p["id"] for p in posts) + 1 if posts else 1
    new_post = {
        "id": new_id,
        "author": post.author,
        "title": post.title,
        "content": post.content,
        "date_posted": datetime.now().strftime("%B %d, %Y"),
    }
    posts.append(new_post)
    return new_post


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
