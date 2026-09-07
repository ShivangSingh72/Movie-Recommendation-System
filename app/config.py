import os
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG_500 = "https://image.tmdb.org/t/p/w500"

if not TMDB_API_KEY:
    # For no crash in production:
    raise RuntimeError("TMDB_API_KEY missing. Put it in .env as TMDB_API_KEY=xxxx")

# Project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# data folder
DATA_DIR = os.path.join(BASE_DIR, "data")

DF_PATH = os.path.join(DATA_DIR, "df.pkl")
INDICES_PATH = os.path.join(DATA_DIR, "indices.pkl")
TFIDF_MATRIX_PATH = os.path.join(DATA_DIR, "tfidf_matrix.pkl")
TFIDF_PATH = os.path.join(DATA_DIR, "tfidf.pkl")