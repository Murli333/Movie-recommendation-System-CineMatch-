from difflib import get_close_matches
import requests
import streamlit as st

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
PLACEHOLDER_POSTER = "https://placehold.co/500x750/1a1a1a/cccccc?text=No+Poster"


def get_api_key():
    """Reads the TMDB key from streamlit secrets."""
    try:
        return st.secrets["TMDB_API_KEY"]
    except Exception:
        return None


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)  # cache for 24 hours
def fetch_poster(movie_title, movie_id_hint=None):
    api_key = get_api_key()
    if not api_key:
        return PLACEHOLDER_POSTER

    try:
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {"api_key": api_key, "query": movie_title}
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            return PLACEHOLDER_POSTER

        poster_path = results[0].get("poster_path")
        if not poster_path:
            return PLACEHOLDER_POSTER

        return TMDB_IMAGE_BASE + poster_path

    except requests.exceptions.RequestException:
        return PLACEHOLDER_POSTER
    except Exception:
        return PLACEHOLDER_POSTER


TMDB_GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance",
    878: "Science Fiction", 10770: "TV Movie", 53: "Thriller", 10752: "War",
    37: "Western"
}


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def fetch_movie_details(movie_title):
   
    defaults = {
        "poster": PLACEHOLDER_POSTER,
        "rating": None,
        "overview": "No overview available.",
        "year": None,
        "genres": [],
        "tmdb_url": None,
        "tmdb_id": None,
    }

    api_key = get_api_key()
    if not api_key:
        return defaults

    try:
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {"api_key": api_key, "query": movie_title}
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            return defaults

        movie = results[0]
        poster_path = movie.get("poster_path")
        release_date = movie.get("release_date", "")
        movie_id = movie.get("id")
        genre_ids = movie.get("genre_ids", [])

        return {
            "poster": TMDB_IMAGE_BASE + poster_path if poster_path else PLACEHOLDER_POSTER,
            "rating": round(movie.get("vote_average", 0), 1),
            "overview": movie.get("overview") or "No overview available.",
            "year": release_date[:4] if release_date else None,
            "genres": [TMDB_GENRE_MAP.get(gid, "") for gid in genre_ids if TMDB_GENRE_MAP.get(gid)],
            "tmdb_url": f"https://www.themoviedb.org/movie/{movie_id}" if movie_id else None,
            "tmdb_id": movie_id,
        }

    except Exception:
        return defaults


def recommend(movies, movies_indices, similarity, movie_name=None, genre=None,
               cutoff=0.6, n_suggestions=3, top_n=20):

    def genre_filter(g):
        if isinstance(g, list):
            return genre.lower() in [x.lower() for x in g]
        return False

    # genre only mode 
    if genre and not movie_name:
        genre_movies = movies[movies['genres'].apply(genre_filter)]
        if genre_movies.empty:
            return {
                "status": "not_found",
                "message": f"No movies found for genre '{genre}'.",
                "matched_title": None,
                "correction_note": None,
                "recommendations": []
            }
        return {
            "status": "ok",
            "matched_title": None,
            "correction_note": None,
            "message": None,
            "recommendations": genre_movies['title'].head(top_n).tolist()
        }
    # exact match check 
    if movie_name in movies_indices:
        matched_name = movie_name
        correction_msg = None
    else:
        # fuzzy match for typos 
        close = get_close_matches(
            movie_name,
            list(movies_indices.keys()),
            n=n_suggestions,
            cutoff=cutoff
        )
        if not close:
            return {
                "status": "not_found",
                "message": f"Movie '{movie_name}' not found and no close matches.",
                "matched_title": None,
                "correction_note": None,
                "recommendations": []
            }
        matched_name = close[0]
        correction_msg = (
            f"'{movie_name}' not found. Did you mean '{matched_name}'?"
            + (f" Other close matches: {close[1:]}" if len(close) > 1 else "")
        )

    #  similarity based recommendations
    idx = movies_indices[matched_name]
    sim_scores = sorted(list(enumerate(similarity[idx])), key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:41]  # top 40 candidates to leave room for genre filtering
    recommended_movies = movies.iloc[[i[0] for i in sim_scores]]

    #  apply genre filter if provided
    if genre:
        recommended_movies = recommended_movies[
            recommended_movies['genres'].apply(genre_filter)
        ]

    recs = recommended_movies['title'].head(top_n).tolist()

    if not recs:
        return {
            "status": "not_found",
            "message": f"No '{genre}' movies found similar to '{matched_name}'. Try a different genre.",
            "matched_title": matched_name,
            "correction_note": correction_msg,
            "recommendations": []
        }

    return {
        "status": "corrected" if correction_msg else "ok",
        "matched_title": matched_name,
        "correction_note": correction_msg,
        "message": None,
        "recommendations": recs
    }