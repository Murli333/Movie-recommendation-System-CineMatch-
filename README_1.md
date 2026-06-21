# 🎬 CineMatch

CineMatch is a content-based movie recommendation system that suggests similar movies based on user preferences. The application uses precomputed similarity scores and integrates with TMDB to display movie posters, ratings, release years, and descriptions in a cinema-themed Streamlit interface.

## Features

### Movie Recommendations

* Get up to 20 similar movie recommendations based on a selected movie.
* Fuzzy matching support for handling spelling mistakes and typos.
* Browse recommendations by genre.
* Combine movie and genre filters for more precise suggestions.

### Rich Movie Information

* Movie posters fetched directly from TMDB.
* Release year and rating displayed for each recommendation.
* Movie overview available on hover.
* Direct links to TMDB movie pages.

### Performance Optimizations

* Poster and metadata caching to reduce API requests.
* Graceful fallback to placeholder posters when TMDB data is unavailable.
* Application remains functional even without a TMDB API key.

---

## Project Structure

```text
CineMatch/
├── app.py
├── recommend.py
├── movies.pkl
├── similarity.pkl
├── dataset.csv
├── real.ipynb
└── .streamlit/
    └── secrets.toml
```

### File Descriptions

**app.py**

* Streamlit frontend application.
* Handles user interaction and displays recommendations.

**recommend.py**

* Core recommendation engine.
* Performs movie matching, similarity lookup, and TMDB API integration.

**movies.pkl**

* Processed movie dataset.

**similarity.pkl**

* Precomputed similarity matrix used for recommendations.

**dataset.csv**

* Raw movie dataset used during preprocessing.

**real.ipynb**

* Jupyter Notebook containing data cleaning, preprocessing, feature engineering, and similarity matrix generation.

---

## Installation

### Clone the Repository

```bash
git clone <repository-url>
cd CineMatch
```

### Install Dependencies

```bash
pip install streamlit pandas requests scikit-learn numpy
```

---

## TMDB API Setup

Create a free account on TMDB and generate an API key.

Create the file:

```text
.streamlit/secrets.toml
```

Add:

```toml
TMDB_API_KEY = "YOUR_API_KEY"
```

> Do not commit this file to GitHub.

---

## Running the Application

```bash
streamlit run app.py
```

The application will automatically open in your browser.

---

## Recommendation Workflow

1. User selects a movie.
2. The recommendation engine finds similar movies using the precomputed similarity matrix.
3. Fuzzy matching handles spelling mistakes.
4. TMDB API retrieves posters and movie metadata.
5. Results are displayed in a responsive movie-card layout.

---

## Tech Stack

* Python
* Pandas
* Scikit-Learn
* Streamlit
* TMDB API
* Pickle

---

## Future Improvements

* Hybrid recommendation system (Content-Based + Collaborative Filtering)
* User authentication
* Personalized watchlists
* Trending and popular movie sections
* Recommendation explanations
* Cloud deployment

---

## Author

**Murli Mishra**

B.Tech CSE (AI) | PSIT Kanpur

Built as a machine learning project to explore recommendation systems, feature engineering, and interactive web deployment using Streamlit.
