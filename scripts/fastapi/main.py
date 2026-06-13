from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()  # create instance of FastAPI

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


@app.get(
    "/", response_class=HTMLResponse, include_in_schema=False
)  # define a route for the root endpoint
@app.get(
    "/posts", response_class=HTMLResponse, include_in_schema=False
)  # stack routes to the same function
def home():
    return f"<h1>{posts[0]['title']}</h1>"


@app.get("/api/posts")
def get_posts():
    return posts
