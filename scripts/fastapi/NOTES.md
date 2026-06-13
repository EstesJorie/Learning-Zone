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
