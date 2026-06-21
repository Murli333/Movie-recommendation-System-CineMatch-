# 🎬 CineMatch

A movie recommender I built that suggests similar movies based on what you like — with real posters, ratings, and info pulled live from TMDB. Wrapped it in a cinema-themed UI because why not make it look cool while it's at it.

## What it actually does

- Pick a movie you like, and it'll show you 20 similar ones
- Typo the movie name? No problem, it auto-corrects to the closest match
- Want to browse by genre instead? You can do that too
- Or combine both — pick a movie AND a genre to narrow things down
- Every recommendation comes with a poster, year, rating, and a short overview that pops up on hover
- Click any poster and it takes you straight to that movie's TMDB page

## How it works (in plain terms)

There are two main files:

**`recommend.py`** — this is the logic. It takes your movie/genre choice and figures out what to recommend using a similarity score (computed beforehand). It also handles the typo correction and talks to TMDB's API to grab posters and details.

**`app.py`** — this is the actual web page you see, built with Streamlit. Sidebar for picking your movie/genre, a button to hit, and a grid of movie cards that show up after.

## Setup

You'll need a few files in your project folder:

```
your_project/
├── app.py
├── recommend.py
├── movies.pkl
├── similarity.pkl
├── dataset.csv
├── real.ipynb
└── .streamlit/
    └── secrets.toml
```

`movies.pkl` and `similarity.pkl` are the dataset + similarity matrix you already had from your notebook.

There's also a `dataset.csv` (the raw movie data this whole thing is built on) and a `notebook.ipynb` — that's the Jupyter notebook where I worked out the data cleaning, genre formatting, and similarity matrix logic before turning it into the `recommend.py` function. Good place to look if you ever want to see how the recommendations are actually calculated under the hood, or if you want to retrain/rebuild the `.pkl` files from scratch.

### 1. Install the stuff you need

```bash
pip install streamlit pandas requests
```

### 2. Get a TMDB API key

Go to [themoviedb.org](https://www.themoviedb.org/), make a free account, and grab an API key from your account settings. This is what lets the app fetch real posters and movie info.

### 3. Add your key

Create a file at `.streamlit/secrets.toml` and put this inside:

```toml
TMDB_API_KEY = "your_actual_key_here"
```

Don't share this file or push it to GitHub — it's basically a password.

### 4. Run it

```bash
streamlit run app.py
```

That's it, it should open in your browser.

## A couple things worth knowing

- Posters are cached for 24 hours so it doesn't keep hammering the TMDB API for the same movie over and over
- If TMDB can't find a poster for something, it shows a placeholder instead of breaking
- If you don't add an API key, the app still runs — it just shows placeholder posters everywhere

## Built by

**Murli Mishra**
📞 +91 93056 93867
📧 mishramurli76@gmail.com
