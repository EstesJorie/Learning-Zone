# FastAPI

Python web-framework for creating APIs.

## Getting Started

First, we need to install FastAPI. We are using `uv` in this project so run:

``zsh
uv add "fastapi[standard]"
```

To start, in a `main.py` file we nede to import FastAPI and create an instance of it

```python
from fastapi import FastAPI

app = FastAPI()
```

FastAPI uses decorators for API routes. In the example below we are using the GET decorator to decorate this `home` function at the root endpoint of our application.

```python
@app.get("/")
def home():
    return{"message": "Hello, World!"}
```

Here we are returning a **dict** which FastAPI will automatically convert to a JSON response. We can run our FastAPI application via the FastAPI CLI:

```zsh
uv run fastapi dev main.py
```

If you go to `localhost:8000/docs` you will see automatically generated Swagger UI documentation for your FastAPI application. You can also go to `localhost:8000/redoc` to get a more modern style API specification/documentation site.

We will use this temporary list of posts to create a new endpoint.

```python
posts: list[dict] = [
    {
        "id": 1,
        "author": "Joe Bloggs",
        "title": "FastAPI rules!",
        "content": "This was really easy to use and super fast.",
        "date_posted": "June 15, 2026"
    },
    {
        "id": 2,
        "author": "Joe Floggs",
        "title": "Python is great for this",
        "content": "Python is a good choice for web development backends.",
        "date_posted": "June 14, 2026"
    },
]

@app.get("/api/posts")
def get_all_posts():
    return posts
```

We create a new endpoint `/api/posts` which calls the function `get_all_posts()`. By default, FastAPI will return the ***posts*** list as a JSON array. Lets go to this new endpoint `localhost:8000/api/posts`, which will see the following:

```json
[
  {
    "id": 1,
    "author": "Joe Bloggs",
    "title": "FastAPI rules!",
    "content": "This was really easy to use and super fast.",
    "date_posted": "June 15, 2026"
  },
  {
    "id": 2,
    "author": "Joe Floggs",
    "title": "Python is great for this",
    "content": "Python is a good choice for web development backends.",
    "date_posted": "June 14, 2026"
  }
]
```

This is brilliant for programmatic access, but when we (as humans) want to look at the data it can get messy and complicated! Let's return some HTML instead! We wil the `HTMLResponse` from FastAPI, so lets import it:

```python
from fastapi.responses import HTMLResponse
```

With this we can update that `home` route to return some HTML:

```python
@app.get("/", response_class=HTMLResponse)
def home():
    return f"<h1>{posts[0]['title']}</h1>"
```

Here, we set the response class of the endpoint to be a HTML Response, and we update the return statement to return the title of the first post in our `posts` dict. In FastAPI we can stack decorators ontop of each to serve the same infromation at different endpoints. For instance, let's say we want to return the HTML response at both the root endpoint `"/"` and a new posts endpoint `"/posts"`, we can do this:

```python
@app.get("/", response_class=HTMLResponse)
@app.get("/posts", response_class=HTMLResponse)
def home():
    return f"<h1>{posts[0]['title']}</h1>"
```

One issue that is arising is that our API documentation has these two HTML response endpoints in them. However, API documentation are really designed for JSON APIs so we can pass a parameter to our HTML response routes called `include_in_schema=False` which will hide these endpoints from our documentation.

>Note: This is just the standard, it does not mean you have to hide them!

## Templates in FastAPI (Jinja2)

Templates allow us to write proper HTML files where we can pass in our dynamic data. `Jinja2` provides HTML templates and is included in `fastapi[standard]`. Jinja2 templates require us to use the `Request` object, and we need to import the templates themselves:

```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
```

To set up our templates we need to create the directory for these templates `/templates`, and then point Jinja2Templates at them.

```python
templates = Jinja2Templates(directory="templates")
```

Now lets create our first tempalte under `templates/home.html`:

```html
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>FastAPI Blog</title>
    </head>
    <body>
        <h1>Welcome</h1>
        <p>This is using a template!.</p>
    </body>
</html>
```

Lets use this template:

```python
@app.get(
    "/", include_in_schema=False
)
@app.get(
    "/posts", include_in_schema=False
)
def home(request: Request):  # define the function to handle the request
    return templates.TemplateResponse(request, "home.html", {"posts": posts})
```

Here, we need to add the `Request` parameter as an argument as it is required by Jinja2. With this we can then return our template via the `templates.TemplateResponse()`. Here, we pass a context dictionary as an argument which means that our template can use different types of variables (i.e our `posts` data).

To actually use this data in our template, we can use the `{% %}` and `{{}}`templating syntax.

```html
    <body>
        <h1>Welcome</h1>
        {% for post in posts %}
            <h2>{{ post.title }}</h2>
            <p>{{ post.content }}</p>
        {% endfor %}
    </body>
```

Here, the `{% %}` to loop through the items within our `posts` list of dictionaries. The `{{}}` allows us to access individual attributes of the variable. We can also conditionally render elements on our page, for instance the page title:

```html
    <head>
        <title>
            {% if title %}
                FastAPI Blog - {{ title }}
            {% else %}
                FastAPI App
            {% endif %}
        </title>
    </head>
```

If the title variable exists, and is passed in the context dictionary then we can dynamically render the page title. If not it will just default to *FastAPI App*.

### Template Inheritance

Tempate inheritance allows us to create a Parent template, which Child templates inherit and fill in specific details. In the below example `layout.html` uses a block which ensures that child tempates can overwrite the content of the ***content*** block.

```html
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>
            {% if title %}
                FastAPI Blog - {{ title }}
            {% else %}
                FastAPI App
            {% endif %}
        </title>
    </head>
    <body>
        {% block content %}
        {% endblock content %}
    </body>
</html>
```

Now we can significantly reduce the content in the origin `home.html` to inherit from our new layout parent file.

```html
{% extends "layout.html" %}
{% block content %}
    {% for post in posts %}
        <h2>{{ post.title }}</h2>
        <p>{{ post.content }}</p>
    {% endfor %}
{% endblock content %}
```

First of all, we extend the layout file via the `extends "layout.html"` and tell it what we are overriding the content block with, in this case our for loop to display the posts.

To mount `static` files to our application we need to import the `StaticFiles` object from FastAPI.

```python
from fastapi.staticfiles import StaticFiles

static_dir = "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
```

This `mount` method takes three arguments; the first is the URL where the static files will be located, the second is the instance of the StaticFiles object which we are using to point at our static directory, and the third is the name which we can use as a reference in our templates.

## Path Parameters

Path paramaters help to grab specifc parts of data, instead of returning all info at once.

```python
@app.get("/api/posts/{post_id}")
def get_post(post_id: int):
    for post in posts:
        if post.get("id") == post_id:
            return post
    return {"error": "Post not found"}
```

In the above example we create a new path, to return a specific post at a specifed post id. The `{post_id}` is the Path parameter which tells FastAPI it is part of the URL which is a variable. Whatever value we enter there is then pased into function as the variable `post_id`. The type hint allows us to automatically validate that the input is correct.

### Error Handling

One major issue arises from this `return {"error": "Post not found"}` as if we go to an post id that does not exist, it will still return a 200 SUCCESS message. This behaviour is contradictory and rather confusing as we would expect it return an error. Lets import the `HTTPExecption` and `status` objects from FastAPI to ensure we correctly raise the error. The `HTTPException` is used to return correct HTTP error responses, and `status` provides us with a list of HTTP status codes.

```python
@app.get("/api/posts/{post_id}")
def get_post(post_id: int):
    for post in posts:
        if post.get("id") == post_id:
            return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
```

Now, we can make this response look more human readable by using HTML, and some more FastAPI objects. First, lets create our error page

```html
{% extends "layout.html" %}
{% block content %}
  <article class="content-section py-3 px-4 mb-4">
    <h1>
      <a class="article-title" href="#">Oops... {{ status_code }} Error</a>
    </h1>
    <p class="article-content">{{ message }}</p>
  </article>
{% endblock content %}
```

Then we will need the following new imports:

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
```

We give the Starlette HTTP exception an alias as to not confuse it with the FastAPI HTTPException we used earlier. We can create a general http exception handler using this Starlette HTTP Exception:

```python
@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exc: StarletteHTTPException):
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
        status_code=exc.status_code
    )
```

We use the `@app.exception_handler` decorator to capture a Starlette HTTP Exception. We set a message that is equal to the detail of the exception if provided and falls back to a default if not. We then check to see if the URL path starts with `/api` and if so we return a JSON response. If is not an API response then we return our HTML error template.

However, this exception handler we only handle HTTP exceptions. We will need a separate handler for *validation errors*.

```python
@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
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
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )
```

## Validation via Pydantic

We can use Pydantic schemas to validate our requests and responses. Pydantic is a data validation library that uses Python type hints. These type hints are enforced at runtime and ensure errors are accurate and detailed. Pydantic integrates very well with FastAPI.

Lets create the schemas that which we can then use in our FastAPI responses. We typically do this in a separate file (`schemas.py`) and then import our schemas throughout our application code.

```python
from pydantic import BaseModel, ConfigDict, Field
```

`BaseModel` is the base class that all of our Pydantic models inherit from, `Field` lets us add constraints, and `ConfigDict` is how we configure our models. Lets create the base model for a post for our application. This *base* model is the definition of what a post is and what is required to make something a post.

```python
class PostBase(BaseModel):
    """Base model for a post."""
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=50)

class PostCreate(PostBase):
    """Model for creating a new post."""
    pass
```

Here, we are utilising the `Field` object to ensure that our model attributes meet specific conditions. Also, note that we are not providing any default values, so all of these parameters are required by default. We'll also create a response model:

```python
class PostResponse(PostBase):
    """Model for responding with a post."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    date_posted: str
```

Currently, our posts are dictionaries and as such we access it with `[]` syntax. But, when we use a database we access the data via dot notation so adding the `from_attributes` allows it to read from objects via the dot notation.

With our schemas defined, lets update our endpoints in `main.py `

```python
from schemas import from schemas import PostCreate, PostResponse

...

@app.get("/api/posts", response_model=list[PostResponse])
def get_posts():
    return posts


@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int):
    for post in posts:
        if post.get("id") == post_id:
            return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
```

Here, we add this `response_model` to our decorators which ensures that any responses at these API endpoints adhere to the expected behaviour that we have set.

So far we have create endpoints to get data, but we can also create new entries or POST data to our application/databse.

```python
@app.post(path="/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate):
    """Create a new post.

    Args:
        post (PostCreate): The post data to create.

    Returns:
        PostResponse: The created post.
    """
    new_id = max(p['id'] for p in posts) + 1 if posts else 1
    new_post = {
        "id": new_id,
        "author": post.author,
        "title": post.title,
        "content": post.content,
        "date_posted": datetime.now().strftime("%B %d, %Y"),
    }
    posts.append(new_post)
    return new_post
```

Here, we use the `PostCreate` model that we defined earlier to ensure that any new posts adhere to the correct format. Note, that we are using a docustring to give our function information. This will appear onto our documentation which also helps to remove ambiguity so that users to use our API correctly.

## Using a Database

Up until now we have been using the hardcoded lists of posts. Lets fix that! We are going to use an SQLite database, and we will talk to it with SQLAlchemy.

```python
uv add sqlalchemy
```

To setup our database, we will need to create a `database.py` to hold all of our database setup code.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite:///./blog.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass

def get_db():
    """Get a database session.

    Yields:
        Session: A SQLAlchemy session.
    """
    with SessionLocal() as db:
        yield db
```

Here, we are setting up the parameters of our database. The `SessionLocal` is a factory that creates sessions between us and our databases. The `get_db()` function allows our routes to get sessions with the database.

Now, we need to create the database models that our API will interact with. First, lets create our `models.py` file and set up our imports:

```python
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
```

We can now define our database models (`models.py`):

```python
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
    image_file: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)

    posts: Mapped[list[Post]] = relationship("Post", back_populates="author") # 1 to many relationship

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
    date_posted: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    author: Mapped[User] = relationship("User", back_populates="posts")  # many to 1 relationship
```

These are the base models for both Users and Posts that our SQLite database will use to store our users and their posts. Now, we need to update our schemas to ensure that we are adhering to new models we have created in our database.

```python
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

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    image_file: str | None
    image_path: str

...

class PostResponse(PostBase):
    """Model for responding with a post."""

    model_config = ConfigDict(
        from_attributes=True
    )  # we can read data from attributes of an object, not just dicts

    id: int  # scoped to class, typically we avoid id in Python
    user_id: int
    date_posted: datetime
    author: UserResponse
```

Here, we are adding a new base model for Users, and just like for posts we create a UserCreate and a UserResponse model. We also need to update our PostResponse as we now expect more infromation for a PostReponse, such as the `user_id` of who posted it, the `date_posted` needs to be a datetime object instead of a fixed date, and the author is a `UserResponse` object as we set up a relationship between the Users and the Posts in our database.

Now we are ready to get our database up and going. In `main.py` we are going to need a few more imports:

```python
from typing import Annotated

from fastapi import Depends

from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from database import Base, engine, get_db
```

With these imports we are importing the tools and models necessary to safely and correctly initalise our new database. First of which, we need to ensure that we create any of our tables that uses our `Base` model. To do this we add:

```python
Base.metadata.create_all(bind=engine)
```

This creates the tables if they do not exist, and is idempotent which ensures that the same action is repeatble on launch of our application. We also need to ensure our media folder is mounted into our app:

```python
media_dir = "media"
if not os.path.isdir(media_dir):
    try:
        os.makedirs(media_dir)
    except Exception as e:
        raise ValueError(
            f"Failed to create media directory '{media_dir}'. Please ensure the application has the necessary permissions. Error: {e}"
        )
app.mount("/media", StaticFiles(directory=media_dir), name="media")
```

We use a try/except block to ensure that we can safely create the missing media folder, and safely fallback if it not possible. We will need a new route to create a user in our database:

```python
@app.post(
    path="/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    """Create a new user."""

    result = db.execute(select(models.User).where(models.User.username == user.username))
    existing_user = result.scalars().first # gets first User obj or None if no match

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    result = db.execute(select(models.User).where(models.User.email == user.email))
    existing_email = result.scalars().first

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    new_user = models.User(
        username = user.username,
        email = user.email,
    )
    db.add(new_user) # stages insert
    db.commit() # executes insert
    db.refresh(new_user) # reloads obj from db

    return new_user
```

Here, we create a new database session via the `Annotated`, which relies on depdendecy injection by calling the `get_db` function and passing its result as the `db` variable here. We then perform two validation steps to ensure the new user has a unique username and a unique email. If successful, we will then create the new user, stage the insert to the database, insert it, and return the new_user as the result. We can also do the same thing with getting a new user:

```python
@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    """Get """

    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first # gets first User obj or None if no match

    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
```

Now, because we have removed the hardcoded list of posts and we are fetching them from the database we need to ensure that our other endpoints have been correctly updated.

```python
@app.get(
    "/", include_in_schema=False, name="home"
)  # define a route for the root endpoint
@app.get(
    "/posts", include_in_schema=False, name="posts"
)  # stack routes to the same function
def home(request: Request, db: Annotated[Session, Depends(get_db)]):  # define the function to handle the request
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


@app.get("/api/posts", response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    """ Retrieve all posts from the database.

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
    name="api_post_detail",
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
```
