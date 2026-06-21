import streamlit as st
import pickle
import pandas as pd
from recommend import recommend, fetch_movie_details, get_api_key

# PAGE CONFIG
st.set_page_config(
    page_title="CineMatch",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# LOAD DATA

@st.cache_data
def load_data():

    movies = pd.read_csv("tmdb_5000_movies.csv")
    credits = pd.read_csv("tmdb_5000_credits.csv")

    movies = movies.merge(credits, on="title")

    # preprocessing
    movies["overview"] = movies["overview"].fillna("")

    movies["genres"] = movies["genres"].apply(convert)
    movies["keywords"] = movies["keywords"].apply(convert)
    movies["cast"] = movies["cast"].apply(convert_cast)
    movies["director"] = movies["crew"].apply(fetch_director)

    movies["tags2"] = (
        movies["genres"].apply(lambda x: " ".join(x))
        + " "
        + movies["keywords"].apply(lambda x: " ".join(x))
        + " "
        + movies["overview"]
    )

    tf = TfidfVectorizer(max_features=5000, stop_words="english")

    v1 = tf.fit_transform(movies["tags2"])

    similarity = cosine_similarity(v1)

    movies_indices = pd.Series(
        movies.index,
        index=movies["title"]
    ).drop_duplicates().to_dict()

    return movies, similarity, movies_indices
movies, similarity, movies_indices = load_data()

# CUSTOM CSS — cinema marquee identity

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/tabler-icons/2.44.0/iconfont/tabler-icons.min.css');

    :root {
        --void: #0a0a0c;
        --surface: #1c1c20;
        --surface-raised: #232328;
        --hairline: #2e2e34;
        --cream: #f4f1e8;
        --cream-dim: #a8a59c;
        --marquee-red: #e8482c;
        --marquee-red-dim: rgba(232, 72, 44, 0.16);
        --brass: #d4a843;
        --brass-dim: rgba(212, 168, 67, 0.14);
    }

    .stApp {
        background:
            radial-gradient(circle at 15% 0%, rgba(232,72,44,0.05) 0%, transparent 45%),
            radial-gradient(circle at 85% 10%, rgba(212,168,67,0.04) 0%, transparent 40%),
            var(--void);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ---------------- MARQUEE HERO ---------------- */
    .marquee-frame {
        position: relative;
        border: 2px solid var(--hairline);
        border-radius: 4px;
        padding: 36px 24px 30px 24px;
        margin: 4px 0 28px 0;
        background: linear-gradient(180deg, #111114 0%, var(--void) 100%);
        overflow: hidden;
    }
    .marquee-frame::before, .marquee-frame::after {
        content: '';
        position: absolute;
        top: 10px; bottom: 10px;
        width: 14px;
        background-image: radial-gradient(circle, var(--void) 3.5px, var(--hairline) 4px, var(--hairline) 4.5px, transparent 4.5px);
        background-size: 14px 22px;
        background-repeat: repeat-y;
    }
    .marquee-frame::before { left: 0; }
    .marquee-frame::after { right: 0; }

    .chase-border {
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        overflow: hidden;
    }
    .chase-border span {
        position: absolute;
        width: 22px; height: 3px;
        background: var(--marquee-red);
        animation: chase 3.2s linear infinite;
        box-shadow: 0 0 6px var(--marquee-red);
    }
    @keyframes chase {
        0% { left: -22px; }
        100% { left: 100%; }
    }

    .hero-wrap {
        text-align: center;
        padding: 4px 28px 0 28px;
        position: relative;
        z-index: 1;
    }
    .hero-eyebrow {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        letter-spacing: 3px;
        color: var(--marquee-red);
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .hero-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 72px;
        letter-spacing: 6px;
        color: var(--cream);
        margin: 0;
        line-height: 1;
        text-shadow: 0 0 24px rgba(244,241,232,0.12);
    }
    .hero-title span { color: var(--marquee-red); }
    .hero-subtitle {
        color: var(--cream-dim);
        font-size: 14.5px;
        margin-top: 10px;
        letter-spacing: 0.4px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ---------------- SIDEBAR ---------------- */
    section[data-testid="stSidebar"] {
        border-right: 1px solid var(--hairline);
    }
    section[data-testid="stSidebar"] .stMarkdown h3 {
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: var(--cream-dim);
    }

    /* ---------------- SECTION HEADERS ---------------- */
    .section-row {
        display: flex;
        align-items: baseline;
        gap: 12px;
        margin: 4px 0 2px 0;
    }
    .section-ticket {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: var(--void);
        background: var(--brass);
        padding: 2px 8px;
        border-radius: 3px;
        letter-spacing: 1px;
        font-weight: 600;
    }
    .section-header {
        font-size: 22px;
        font-weight: 700;
        color: var(--cream);
        margin: 0;
    }
    .section-caption {
        color: var(--cream-dim);
        font-size: 13.5px;
        margin: 6px 0 22px 0;
        font-family: 'JetBrains Mono', monospace;
    }
    .section-caption b { color: var(--cream); font-weight: 500; }

    /* ---------------- MOVIE CARD (ticket stub) ---------------- */
    .movie-card {
        position: relative;
        background: var(--surface);
        border: 1px solid var(--hairline);
        border-radius: 6px;
        overflow: hidden;
        transition: transform 0.3s cubic-bezier(.2,.8,.2,1), border-color 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
        text-decoration: none;
        display: block;
        cursor: pointer;
    }
    .movie-card:hover {
        transform: translateY(-8px);
        border-color: var(--marquee-red);
        box-shadow: 0 18px 36px rgba(0,0,0,0.45), 0 0 0 1px rgba(232,72,44,0.3);
    }
    .movie-card:focus-visible {
        outline: 2px solid var(--brass);
        outline-offset: 2px;
    }

    /* ticket notch */
    .movie-card::before {
        content: '';
        position: absolute;
        top: calc(133.33% - 9px);
        left: -9px;
        width: 18px; height: 18px;
        background: var(--void);
        border-radius: 50%;
        z-index: 3;
    }
    .movie-card::after {
        content: '';
        position: absolute;
        top: calc(133.33% - 9px);
        right: -9px;
        width: 18px; height: 18px;
        background: var(--void);
        border-radius: 50%;
        z-index: 3;
    }

    .poster-wrap {
        position: relative;
        width: 100%;
        aspect-ratio: 2 / 3;
        overflow: hidden;
    }
    .movie-poster {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
        transition: transform 0.4s ease, filter 0.4s ease;
        filter: saturate(0.92);
    }
    .movie-card:hover .movie-poster {
        transform: scale(1.07);
        filter: saturate(1.05);
    }

    .poster-overlay {
        position: absolute;
        inset: 0;
        background: linear-gradient(180deg, rgba(10,10,12,0.1) 0%, rgba(10,10,12,0.97) 76%);
        opacity: 0;
        transition: opacity 0.28s ease;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        padding: 14px;
    }
    .movie-card:hover .poster-overlay {
        opacity: 1;
    }
    .overlay-overview {
        color: var(--cream-dim);
        font-size: 11.5px;
        line-height: 1.55;
        margin-bottom: 10px;
        display: -webkit-box;
        -webkit-line-clamp: 6;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .overlay-genres {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
        margin-bottom: 9px;
    }
    .genre-chip {
        background: var(--marquee-red-dim);
        color: #ff8a73;
        font-size: 10px;
        font-weight: 600;
        padding: 2px 7px;
        border-radius: 3px;
        letter-spacing: 0.3px;
        font-family: 'JetBrains Mono', monospace;
    }
    .overlay-cta {
        display: flex;
        align-items: center;
        gap: 6px;
        color: var(--brass);
        font-size: 11.5px;
        font-weight: 600;
        letter-spacing: 0.4px;
        font-family: 'JetBrains Mono', monospace;
    }

    .movie-info {
        padding: 16px 14px 14px 14px;
        position: relative;
    }
    .movie-info::before {
        content: '';
        position: absolute;
        top: 0; left: 14px; right: 14px;
        border-top: 1px dashed var(--hairline);
    }
    .movie-title {
        font-size: 14.5px;
        font-weight: 600;
        color: var(--cream);
        margin: 0 0 7px 0;
        line-height: 1.3;
        min-height: 38px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .movie-meta {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 12px;
        color: var(--cream-dim);
        font-family: 'JetBrains Mono', monospace;
    }
    .rating-badge {
        background: var(--brass-dim);
        color: var(--brass);
        padding: 2px 8px;
        border-radius: 3px;
        font-weight: 600;
        font-size: 11.5px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    /* ---------------- SKELETON LOADING ---------------- */
    .skeleton-card {
        background: var(--surface);
        border: 1px solid var(--hairline);
        border-radius: 6px;
        overflow: hidden;
        height: 100%;
    }
    .skeleton-poster {
        width: 100%;
        aspect-ratio: 2 / 3;
        background: linear-gradient(100deg, var(--surface) 30%, var(--surface-raised) 50%, var(--surface) 70%);
        background-size: 200% 100%;
        animation: shimmer 1.4s ease-in-out infinite;
    }
    .skeleton-line {
        height: 10px;
        margin: 14px 14px 8px 14px;
        border-radius: 3px;
        background: linear-gradient(100deg, var(--surface) 30%, var(--surface-raised) 50%, var(--surface) 70%);
        background-size: 200% 100%;
        animation: shimmer 1.4s ease-in-out infinite;
    }
    .skeleton-line.short { width: 50%; }
    @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }

    /* ---------------- BUTTONS ---------------- */
    .stButton > button {
        background: var(--marquee-red);
        color: var(--cream);
        font-weight: 700;
        border: none;
        border-radius: 4px;
        padding: 11px 0;
        letter-spacing: 0.6px;
        transition: all 0.2s ease;
        font-family: 'Inter', sans-serif;
    }
    .stButton > button:hover {
        background: #ff5736;
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(232,72,44,0.35);
    }
    .stButton > button:active {
        transform: translateY(0px) scale(0.98);
    }

    /* ---------------- EMPTY / ERROR STATES ---------------- */
    .state-block {
        border: 1px dashed var(--hairline);
        border-radius: 6px;
        padding: 40px 28px;
        text-align: center;
        margin-top: 8px;
    }
    .state-icon {
        font-size: 32px;
        color: var(--cream-dim);
        margin-bottom: 14px;
        display: block;
    }
    .state-title {
        font-size: 17px;
        font-weight: 600;
        color: var(--cream);
        margin-bottom: 6px;
    }
    .state-text {
        font-size: 13.5px;
        color: var(--cream-dim);
        max-width: 420px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* ---------------- MISC ---------------- */
    .block-container { padding-top: 1.5rem; }
    hr { border-color: var(--hairline) !important; }

    /* ---------------- FOOTER CREDITS ---------------- */
    .credits-roll {
        position: relative;
        margin-top: 48px;
        padding: 28px 24px 22px 24px;
        border-top: 1px solid var(--hairline);
        text-align: center;
        overflow: hidden;
    }
    .credits-roll::before {
        content: '';
        position: absolute;
        top: -1px; left: 50%;
        transform: translateX(-50%);
        width: 60px; height: 1px;
        background: var(--marquee-red);
        box-shadow: 0 0 8px var(--marquee-red);
    }
    .credits-eyebrow {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        letter-spacing: 3px;
        color: var(--cream-dim);
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    .credits-name {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 26px;
        letter-spacing: 2.5px;
        color: var(--cream);
        margin-bottom: 14px;
    }
    .credits-links {
        display: flex;
        justify-content: center;
        gap: 10px;
        flex-wrap: wrap;
    }
    .credit-pill {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12.5px;
        color: var(--cream-dim);
        background: var(--surface);
        border: 1px solid var(--hairline);
        padding: 7px 14px;
        border-radius: 20px;
        text-decoration: none;
        transition: border-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
    }
    .credit-pill:hover {
        border-color: var(--marquee-red);
        color: var(--cream);
        transform: translateY(-2px);
    }
    .credit-pill i {
        font-size: 14px;
        color: var(--brass);
    }
    .credits-tagline {
        margin-top: 16px;
        font-size: 11px;
        color: var(--cream-dim);
        opacity: 0.6;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.5px;
    }

    @media (prefers-reduced-motion: reduce) {
        .chase-border span, .skeleton-poster, .skeleton-line { animation: none !important; }
        .movie-card, .movie-poster { transition: none !important; }
    }
</style>
""", unsafe_allow_html=True)

# HERO HEADER — marquee with chasing light border
st.markdown("""
<div class="marquee-frame">
    <div class="chase-border"><span></span></div>
    <div class="hero-wrap">
        <div class="hero-eyebrow">Now showing</div>
        <div class="hero-title">CINE<span>MATCH</span></div>
        <div class="hero-subtitle">// find your next favorite movie, instantly</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Warn if API key missing, but don't block the app
if not get_api_key():
    st.info("Posters are showing as placeholders — add your TMDB API key to `.streamlit/secrets.toml` as `TMDB_API_KEY` to enable them.")


# SIDEBAR — SEARCH CONTROLS

all_genres = sorted(set(
    genre.strip().strip("'")
    for genres in movies['genres'].dropna()
    for genre in (genres if isinstance(genres, list) else [])
))

with st.sidebar:
    st.markdown("### Search options")
    mode = st.radio(
        "How do you want to search?",
        ["By movie", "By genre", "Movie + genre"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    movie_input = None
    genre_input = None

    if mode == "By movie":
        movie_input = st.selectbox("Pick a movie you like", movies['title'].values)

    elif mode == "By genre":
        genre_input = st.selectbox("Pick a genre", all_genres)

    elif mode == "Movie + genre":
        movie_input = st.selectbox("Pick a movie you like", movies['title'].values)
        genre_choice = st.selectbox("Narrow down by genre", ["All"] + all_genres)
        genre_input = None if genre_choice == "All" else genre_choice

    st.markdown("---")
    run_search = st.button("Recommend", use_container_width=True)

    st.markdown("---")
    st.caption("Posters powered by TMDB. Typos in movie titles are auto-corrected.")

# MAIN CONTENT — RESULTS
COLS_PER_ROW = 5

def render_skeleton_grid(n=10):
    """Shows shimmering placeholder cards while posters are being fetched."""
    for row_start in range(0, n, COLS_PER_ROW):
        cols = st.columns(COLS_PER_ROW)
        for col in cols:
            with col:
                st.markdown("""
                    <div class="skeleton-card">
                        <div class="skeleton-poster"></div>
                        <div class="skeleton-line"></div>
                        <div class="skeleton-line short"></div>
                    </div>
                """, unsafe_allow_html=True)


if run_search:
    result = recommend(
        movies=movies,
        movies_indices=movies_indices,
        similarity=similarity,
        movie_name=movie_input,
        genre=genre_input
    )

    if result["correction_note"]:
        st.warning(f"📝 {result['correction_note']}")

    if result["status"] == "not_found":
        st.markdown(f"""
            <div class="state-block">
                <i class="ti ti-mood-confuzed state-icon" aria-hidden="true"></i>
                <div class="state-title">No match found</div>
                <div class="state-text">{result['message']} Try a different title or pick another genre from the sidebar.</div>
            </div>
        """, unsafe_allow_html=True)

    elif result["recommendations"]:
        label = result["matched_title"] or genre_input or "your picks"
        st.markdown("""
            <div class="section-row">
                <span class="section-ticket">REC</span>
                <p class="section-header">Recommended for you</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown(f'<div class="section-caption">based on <b>{label}</b></div>', unsafe_allow_html=True)

        recommendations = result["recommendations"]
        placeholder = st.empty()

        # Show skeleton cards immediately so the wait doesn't feel dead
        with placeholder.container():
            render_skeleton_grid(len(recommendations))

        details = [fetch_movie_details(title) for title in recommendations]

        # Replace skeletons with real cards
        with placeholder.container():
            for row_start in range(0, len(recommendations), COLS_PER_ROW):
                row_titles = recommendations[row_start:row_start + COLS_PER_ROW]
                row_details = details[row_start:row_start + COLS_PER_ROW]
                cols = st.columns(COLS_PER_ROW)

                for col, title, info in zip(cols, row_titles, row_details):
                    with col:
                        rating_html = (
                            f'<span class="rating-badge"><i class="ti ti-star-filled" style="font-size:11px"></i> {info["rating"]}</span>'
                            if info["rating"] else ""
                        )
                        year_html = f'<span>{info["year"]}</span>' if info["year"] else "<span></span>"

                        genre_chips = "".join(
                            f'<span class="genre-chip">{g}</span>' for g in info["genres"][:3]
                        )

                        overview_text = info["overview"]
                        if len(overview_text) > 220:
                            overview_text = overview_text[:220].rsplit(" ", 1)[0] + "…"

                        link_url = info["tmdb_url"] or (
                            f"https://www.themoviedb.org/search?query={title.replace(' ', '+')}"
                        )

                        st.markdown(f"""
                            <a class="movie-card" href="{link_url}" target="_blank" rel="noopener noreferrer">
                                <div class="poster-wrap">
                                    <img class="movie-poster" src="{info['poster']}" alt="{title}" loading="lazy">
                                    <div class="poster-overlay">
                                        <div class="overlay-genres">{genre_chips}</div>
                                        <div class="overlay-overview">{overview_text}</div>
                                        <div class="overlay-cta"><i class="ti ti-external-link"></i> View on TMDB</div>
                                    </div>
                                </div>
                                <div class="movie-info">
                                    <p class="movie-title">{title}</p>
                                    <div class="movie-meta">
                                        {year_html}
                                        {rating_html}
                                    </div>
                                </div>
                            </a>
                        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="state-block">
                <i class="ti ti-filter-off state-icon" aria-hidden="true"></i>
                <div class="state-title">Nothing matches these filters</div>
                <div class="state-text">Try loosening the genre filter or pick a different movie to compare against.</div>
            </div>
        """, unsafe_allow_html=True)

else:
    # Empty state before first search
    st.markdown("""
        <div class="state-block">
            <i class="ti ti-movie state-icon" aria-hidden="true"></i>
            <div class="state-title">Ready when you are</div>
            <div class="state-text">Pick a movie, a genre, or both from the sidebar, then hit <b>Recommend</b> to roll the reel.</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("""
    <div class="credits-roll">
        <div class="credits-eyebrow">Directed &amp; built by</div>
        <div class="credits-name">MURLI MISHRA</div>
        <div class="credits-links">
            <a class="credit-pill" href="tel:+919305693867">
                <i class="ti ti-phone" aria-hidden="true"></i> +91 93056 93867
            </a>
            <a class="credit-pill" href="mailto:mishramurli76@gmail.com">
                <i class="ti ti-mail" aria-hidden="true"></i> mishramurli76@gmail.com
            </a>
        </div>
        <div class="credits-tagline">CineMatch — end of reel</div>
    </div>
""", unsafe_allow_html=True)