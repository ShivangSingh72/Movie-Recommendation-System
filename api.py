"""
API client for the Movie Recommender FastAPI backend.

Every function here maps 1:1 to an existing endpoint in app/main.py.
No endpoint names, params, or response shapes are altered.
"""

import os
from typing import Any, Optional

import requests
import streamlit as st

API_BASE = os.environ.get("MOVIE_API_BASE", "https://movie-rec-466x.onrender.com")
TMDB_IMG = "https://image.tmdb.org/t/p/w500"


@st.cache_data(ttl=30, show_spinner=False)
def _get(path: str, params: Optional[dict] = None) -> tuple[Any, Optional[str]]:
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=25)
        if r.status_code >= 400:
            return None, f"HTTP {r.status_code}: {r.text[:300]}"
        return r.json(), None
    except Exception as e:
        return None, f"Request failed: {e}"


def get_home(category: str, limit: int = 24):
    """GET /home"""
    return _get("/home", {"category": category, "limit": limit})


def tmdb_search(query: str):
    """GET /tmdb/search — raw TMDB shape with 'results'."""
    return _get("/tmdb/search", {"query": query})


def get_movie_details(tmdb_id: int):
    """GET /movie/id/{tmdb_id}"""
    return _get(f"/movie/id/{tmdb_id}")


def get_recommend_genre(tmdb_id: int, limit: int = 18):
    """GET /recommend/genre"""
    return _get("/recommend/genre", {"tmdb_id": tmdb_id, "limit": limit})


def get_recommend_tfidf(title: str, top_n: int = 10):
    """GET /recommend/tfidf"""
    return _get("/recommend/tfidf", {"title": title, "top_n": top_n})


def get_search_bundle(query: str, tfidf_top_n: int = 12, genre_limit: int = 12):
    """GET /movie/search — details + TF-IDF recs + genre recs bundle."""
    return _get(
        "/movie/search",
        {"query": query, "tfidf_top_n": tfidf_top_n, "genre_limit": genre_limit},
    )
