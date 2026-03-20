import pandas as pd
import os
from datetime import datetime
import numpy as np
from clean_data import (
    parse_keywords, parse_genres, clean_numeric_column,
    validate_dataframe_ids, calculate_days_since_release,
    validate_date_column, handle_missing_values_columns,
    create_genre_flags
)

RAW_DIR = "../data_collector/raw"
PROCESSED_DIR = "../data_collector/processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)

print("=" * 60)
print("PREPROCESSING FILMS - Chargement et nettoyage des données brutes")
print("=" * 60)

# ========== 1. CHARGEMENT DES DATASETS BRUTS ==========
print("\n1. Chargement des datasets bruts...")
movies = pd.read_csv(f"{RAW_DIR}/movies_metadata.csv", low_memory=False)
keywords = pd.read_csv(f"{RAW_DIR}/keywords.csv")
ratings = pd.read_csv(f"{RAW_DIR}/ratings.csv")
links = pd.read_csv(f"{RAW_DIR}/links.csv")

# ========== 2. NETTOYAGE DES IDs ==========
print("2. Nettoyage et validation des IDs...")
movies = validate_dataframe_ids(movies, 'id')
keywords = validate_dataframe_ids(keywords, 'id')
ratings['movieId'] = clean_numeric_column(ratings['movieId'], fill_value=np.nan)
ratings = ratings.dropna(subset=['movieId'])
ratings['movieId'] = ratings['movieId'].astype(int)
links['tmdbId'] = clean_numeric_column(links['tmdbId'], fill_value=np.nan)
links = links.dropna(subset=['tmdbId'])
links['tmdbId'] = links['tmdbId'].astype(int)

# ========== 3. FUSION KEYWORDS ==========
print("3. Fusion avec keywords...")
keywords_list = keywords['keywords'].apply(parse_keywords)
keywords['keywords_list'] = keywords_list
keywords_group = keywords.groupby('id')['keywords_list'].apply(
    lambda x: list(set(sum(x, [])))
).reset_index()
keywords_group.rename(columns={'keywords_list': 'all_keywords'}, inplace=True)

movies = movies.merge(keywords_group, on='id', how='left')
movies['num_keywords'] = movies['all_keywords'].apply(
    lambda x: len(x) if isinstance(x, list) else 0
)

# ========== 4. FUSION RATINGS ==========
print("4. Fusion avec ratings utilisateur...")
ratings_agg = ratings.groupby('movieId').agg({
    'rating': ['mean', 'count'],
    'userId': 'nunique'
}).reset_index()
ratings_agg.columns = ['movieId', 'avg_user_rating', 'num_ratings', 'num_unique_users']

# Lien via links.csv
ratings_agg = ratings_agg.merge(links[['movieId', 'tmdbId']], on='movieId', how='left')
ratings_agg = ratings_agg.dropna(subset=['tmdbId'])
ratings_agg['tmdbId'] = ratings_agg['tmdbId'].astype(int)

movies = movies.merge(
    ratings_agg[['tmdbId', 'avg_user_rating', 'num_ratings', 'num_unique_users']], 
    left_on='id', right_on='tmdbId', how='left'
)

# ========== 5. PARSING DES GENRES ==========
print("5. Parsing des genres...")
movies['genres_list'] = movies['genres'].apply(parse_genres)
movies['num_genres'] = movies['genres_list'].apply(
    lambda x: len(x) if isinstance(x, list) else 0
)

# ========== 6. NETTOYAGE DES COLONNES NUMÉRIQUES ==========
print("6. Nettoyage des colonnes numériques...")
movies['release_date'] = validate_date_column(movies['release_date'])
movies['budget'] = clean_numeric_column(movies['budget'], fill_value=0)
movies['revenue'] = clean_numeric_column(movies['revenue'], fill_value=0)
movies['runtime'] = clean_numeric_column(movies['runtime'], fill_value=0)
movies['popularity'] = clean_numeric_column(movies['popularity'], fill_value=0)
movies['vote_average'] = clean_numeric_column(movies['vote_average'], fill_value=0)
movies['vote_count'] = clean_numeric_column(movies['vote_count'], fill_value=0)
movies['avg_user_rating'] = clean_numeric_column(movies['avg_user_rating'], fill_value=0)
movies['num_ratings'] = clean_numeric_column(movies['num_ratings'], fill_value=0)
movies['num_unique_users'] = clean_numeric_column(movies['num_unique_users'], fill_value=0)

# ========== 7. CALCULS SIMPLES DE PRÉTRAITEMENT ==========
print("7. Calculs de prétraitement...")

# Jours depuis sortie
movies['days_since_release'] = calculate_days_since_release(movies['release_date'])

# Log transformations simples (pour normaliser les distributions)
movies['log_popularity'] = np.log1p(movies['popularity'])
movies['log_budget'] = np.log1p(movies['budget'])
movies['log_revenue'] = np.log1p(movies['revenue'])
movies['log_vote_count'] = np.log1p(movies['vote_count'])

# ========== 8. CRÉER FLAGS POUR GENRES POPULAIRES ==========
print("8. Création de flags pour genres populaires...")
popular_genres = [
    "Drama", "Comedy", "Action", "Adventure", "Thriller", 
    "Romance", "Horror", "Science Fiction", "Crime", 
    "Animation", "Fantasy", "Mystery", "Family", "Documentary"
]

for genre in popular_genres:
    movies[f'has_{genre.lower().replace(" ", "_")}'] = movies['genres_list'].apply(
        lambda x: genre in x if isinstance(x, list) else False
    )

# ========== 9. SÉLECTION DES COLONNES FINALES ==========
print("9. Sélection des colonnes finales...")

genre_flags = [f'has_{g.lower().replace(" ", "_")}' for g in popular_genres]

final_cols = [
    'id', 'title', 'release_date', 'budget', 'revenue', 'runtime',
    'popularity', 'vote_average', 'vote_count',
    'days_since_release',
    'avg_user_rating', 'num_ratings', 'num_unique_users',
    'num_keywords', 'num_genres',
    'log_popularity', 'log_budget', 'log_revenue', 'log_vote_count'
] + genre_flags

movies_final = movies[final_cols].dropna(subset=['title', 'release_date'])

# ========== 10. EXPORT ==========
print("10. Export du dataset nettoyé...")
output = f"{PROCESSED_DIR}/movies_cleaned_for_ml_{datetime.now():%Y%m%d}.csv"
movies_final.to_csv(output, index=False)

print("\n" + "=" * 60)
print(f"✅ SUCCÈS - {movies_final.shape[0]} films traités")
print(f"📊 Colonnes: {len(final_cols)}")
print(f"💾 Fichier: {output}")
print("=" * 60)
