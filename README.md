<img src="./img/logo.png" alt="Logo" width=125 height=175>

# Learning Zone

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.14%2B-blue)](#)
[![Ruff](https://img.shields.io/badge/style-ruff-black)](#)
[![Pre-Commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](#)
[![UV](https://img.shields.io/badge/Package%20Manager-uv-purple)](#)

This is repo focuses on different areas of learning.

## Installation

Use the package manager [uv](https://docs.astral.sh/uv/) to get started. We have numerous dependency groups within our `pyproject.toml` so use the following command to install the correct group:

```bash
uv sync --frozen --group <group_name>
```
> NOTE: Each `NOTES.MD` should inform you what group to install

## Table of Contents

- [Pydantic V2](./scripts/pydantic//pydantic-NOTES.MD)
- [FastAPI](./scripts/fastapi/NOTES.md)
- [Introduction to NGINX](./scripts/intro-to-nginx/NOTES.md)
- [NGINX and Docker](./scripts/nginx-and-docker/NOTES.md)
