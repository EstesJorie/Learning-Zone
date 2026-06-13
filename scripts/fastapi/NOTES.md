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

## Templates in FastAPI

Templates allow us
