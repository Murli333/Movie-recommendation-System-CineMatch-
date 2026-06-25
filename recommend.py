"""
recommend.py
------------
Backend logic for CineMatch: title resolution (with typo correction),
content-based recommendation (movie / genre / movie+genre), and live
TMDB lookups used to render posters, ratings, and overview text in the UI.

This module has no Streamlit UI code in it on purpose — app.py owns
everything visual; this file only owns data/logic, so the two stay
swappable independently.

Public contract used by app.py:
    get_api_key() -> str | None
    fetch_movie_details(title: str) -> dict
    recommend(movies, movies_indices, similarity, movie_name=None,
              genre=None, top_n=10) -> dict
"""

import os
import difflib
import functools

import pandas as pd
import requests

try:
    import streamlit as st
except ImportError:  # keeps this module importable/testable outside Streamlit
    st = None


TMDB_API_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
PLACEHOLDER_POSTER = "https://via.placeholder.com/500x750/1c1c20/a8a59c?text=No+Poster"
REQUEST_TIMEOUT = 6  # seconds — fail fast rather than hang the UI on a slow request


# ---------------------------------------------------------------------------
# API key
# ---------------------------------------------------------------------------

def get_api_key():
    """
    Looks for a TMDB v3 API key, checking (in order):
      1. st.secrets["TMDB_API_KEY"]   (.streamlit/secrets.toml)
      2. the TMDB_API_KEY environment variable
    Returns None if neither is set — callers must treat that as
    "no live data available" and fall back to placeholders, not crash.
    """
    if st is not None:
        try:
            if "TMDB_API_KEY" in st.secrets and st.secrets["TMDB_API_KEY"]:
                return st.secrets["TMDB_API_KEY"]
        except Exception:
            pass  # no secrets.toml at all — fine, just fall through

    return os.environ.get("TMDB_API_KEY") or None


# ---------------------------------------------------------------------------
# Live TMDB lookups (posters / ratings / overview / genre chips)
# ---------------------------------------------------------------------------

def _placeholder_details():
    return {
        "poster": PLACEHOLDER_POSTER,
        "rating": None,
        "year": None,
        "genres": [],
        "overview": "",
        "tmdb_url": None,
    }


@functools.lru_cache(maxsize=1)
def _genre_id_map(api_key):
    """TMDB's /search/movie only returns genre_ids, not names. Fetch the
    id->name table once per API key and cache it for the process lifetime."""
    try:
        resp = requests.get(
            f"{TMDB_API_BASE}/genre/movie/list",
            params={"api_key": api_key},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return {g["id"]: g["name"] for g in resp.json().get("genres", [])}
    except requests.RequestException:
        return {}


@functools.lru_cache(maxsize=4000)
def _search_tmdb(title, api_key):
    """Cached raw search call — repeated lookups of the same title (e.g.
    re-rendering the same recommendation list) cost one request total."""
    try:
        resp = requests.get(
            f"{TMDB_API_BASE}/search/movie",
            params={"api_key": api_key, "query": title},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return results[0] if results else None
    except requests.RequestException:
        return None


def fetch_movie_details(title):
    """
    Live lookup for a single movie title: poster URL, rating, release year,
    genre names, overview text, and a TMDB page link.

    Never raises — on any failure (no API key, no network, no match) it
    returns the same placeholder shape so the UI always has something
    sane to render.
    """
    api_key = get_api_key()
    if not api_key or not title:
        return _placeholder_details()

    result = _search_tmdb(title, api_key)
    if not result:
        return _placeholder_details()

    poster_path = result.get("poster_path")
    release_date = result.get("release_date") or ""
    genre_map = _genre_id_map(api_key)
    genre_names = [genre_map[g] for g in result.get("genre_ids", []) if g in genre_map]

    return {
        "poster": f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else PLACEHOLDER_POSTER,
        "rating": round(result["vote_average"], 1) if result.get("vote_average") else None,
        "year": release_date[:4] if release_date else None,
        "genres": genre_names,
        "overview": result.get("overview") or "",
        "tmdb_url": f"https://www.themoviedb.org/movie/{result['id']}" if result.get("id") else None,
    }


# ---------------------------------------------------------------------------
# Title resolution (handles typos / case differences)
# ---------------------------------------------------------------------------

def _normalize(text):
    return str(text).strip().lower()


def _resolve_title(movies_indices, movie_name):
    """
    Exact case-insensitive match first. If that fails, fuzzy-match against
    every known title so a typo like "Avtaar" still resolves to "Avatar".
    Returns (resolved_title_or_None, correction_note_or_None).
    """
    if not movie_name:
        return None, None

    lower_to_original = {}
    for t in movies_indices.keys():
        lower_to_original.setdefault(_normalize(t), t)

    query = _normalize(movie_name)
    if query in lower_to_original:
        return lower_to_original[query], None

    close = difflib.get_close_matches(query, list(lower_to_original.keys()), n=1, cutoff=0.6)
    if close:
        matched = lower_to_original[close[0]]
        note = f'Couldn\'t find "{movie_name}" exactly — showing results for "{matched}" instead.'
        return matched, note

    return None, None


# ---------------------------------------------------------------------------
# Weighted rating (IMDB-style), used to rank genre-only requests where
# there's no anchor movie to compute similarity against.
# ---------------------------------------------------------------------------

def _weighted_score(row, m, c):
    v = row.get("vote_count", 0) or 0
    r = row.get("vote_average", 0) or 0
    if (v + m) == 0:
        return 0.0
    return (v / (v + m)) * r + (m / (v + m)) * c


# ---------------------------------------------------------------------------
# Main recommendation entry point
# ---------------------------------------------------------------------------

def recommend(movies, movies_indices, similarity, movie_name=None, genre=None, top_n=10):
    """
    Three modes, dispatched on which of movie_name/genre are given:

    - genre only      -> highest (weighted) rated movies carrying that genre
    - movie only       -> most similar movies by content (cosine similarity)
    - movie + genre    -> most similar movies, restricted to that genre

    Always returns:
        {
            "status": "ok" | "not_found",
            "message": str,                # human-readable, set on not_found
            "matched_title": str | None,   # resolved title, if movie_name given
            "correction_note": str | None, # set if a typo was auto-corrected
            "recommendations": list[str],  # movie titles, possibly empty
        }
    """
    result = {
        "status": "ok",
        "message": "",
        "matched_title": None,
        "correction_note": None,
        "recommendations": [],
    }

    if not movie_name and not genre:
        result["status"] = "not_found"
        result["message"] = "Pick a movie or a genre first."
        return result

    # ---- Genre-only: no anchor movie, rank by weighted rating ----
    if genre and not movie_name:
        mask = movies["genres"].apply(lambda g: genre in g if isinstance(g, list) else False)
        subset = movies[mask]

        if subset.empty:
            result["status"] = "not_found"
            result["message"] = f'No movies found in the "{genre}" genre.'
            return result

        c = pd.to_numeric(movies.get("vote_average", pd.Series(dtype=float)), errors="coerce").mean()
        m = pd.to_numeric(subset.get("vote_count", pd.Series(dtype=float)), errors="coerce").quantile(0.60)

        scored = subset.copy()
        scored["_score"] = scored.apply(lambda r: _weighted_score(r, m, c), axis=1)
        scored = scored.sort_values("_score", ascending=False)

        result["recommendations"] = scored["title"].head(top_n).tolist()
        return result

    # ---- Movie given (optionally narrowed by genre) ----
    resolved, note = _resolve_title(movies_indices, movie_name)
    result["correction_note"] = note

    if resolved is None:
        result["status"] = "not_found"
        result["message"] = f'"{movie_name}" isn\'t in the catalog.'
        return result

    result["matched_title"] = resolved
    idx = movies_indices[resolved]

    scores = sorted(enumerate(similarity[idx]), key=lambda x: x[1], reverse=True)

    picked = []
    for i, _score in scores:
        if i == idx:
            continue  # never recommend the movie back to itself

        if genre:
            row_genres = movies.iloc[i]["genres"]
            if not isinstance(row_genres, list) or genre not in row_genres:
                continue

        picked.append(movies.iloc[i]["title"])
        if len(picked) >= top_n:
            break

    result["recommendations"] = picked
    return result