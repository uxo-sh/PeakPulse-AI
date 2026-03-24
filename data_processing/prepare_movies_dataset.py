import pandas as pd
import os
from datetime import datetime
import numpy as np
from clean_data import (
    clean_numeric_column,
    validate_dataframe_ids, calculate_days_since_release,
    validate_date_column, handle_missing_values_columns,
    create_genre_flags
)

RAW_DATA_PATH = "../data_collector/raw/movies_2024_raw.csv"
PROCESSED_DATA_PATH = "../data_collector/processed/peakpulse_v2_2024.csv"
os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)

print("=" * 60)
print("PREPROCESSING FILMS - Chargement et nettoyage des données brutes")
print("=" * 60)

# ========== 1. CHARGEMENT DES DATASETS BRUTS ==========
print("\n1. Chargement des datasets bruts...")
movies = pd.read_csv(RAW_DATA_PATH, low_memory=False)

# ========== 2. NETTOYAGE DES IDs ==========
print("2. Nettoyage et validation des IDs...")
movies = validate_dataframe_ids(movies, 'id')

# ========== 3. PARSING KEYWORDS ==========
print("3. Parsing keywords...")
# Les keywords sont maintenant des strings séparées par des virgules
movies['keywords_list'] = movies['keywords'].apply(
    lambda x: [k.strip() for k in str(x).split(',')] if pd.notna(x) else []
)
movies['num_keywords'] = movies['keywords_list'].apply(len)

# ========== 4. MAPPING DES RATINGS ==========
print("4. Mapping des ratings...")
# Plus de ratings.csv, on utilise vote_average et vote_count
movies['avg_user_rating'] = movies['vote_average']
movies['num_ratings'] = movies['vote_count']
movies['num_unique_users'] = movies['vote_count'] # Fallback car manque userId

# ========== 5. PARSING DES GENRES ==========
print("5. Parsing des genres...")
# Les genres sont maintenant des strings séparées par des virgules
movies['genres_list'] = movies['genres'].apply(
    lambda x: [g.strip() for g in str(x).split(',')] if pd.notna(x) else []
)
movies['num_genres'] = movies['genres_list'].apply(len)


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
movies['log_days_since_release'] = np.log1p(movies['days_since_release'].clip(lower=0))

# Flag Streaming
streaming_platforms = ['Netflix', 'Amazon', 'Apple', 'Hulu', 'Disney']
movies['is_streaming'] = movies['production_companies'].apply(
    lambda x: 1 if isinstance(x, str) and any(p.lower() in x.lower() for p in streaming_platforms) else 0
)

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
    'days_since_release', 'log_days_since_release', 'is_streaming',
    'avg_user_rating', 'num_ratings', 'num_unique_users',
    'num_keywords', 'num_genres',
    'log_popularity', 'log_budget', 'log_revenue', 'log_vote_count'
] + genre_flags

movies_final = movies[final_cols].dropna(subset=['title', 'release_date'])

# ========== 10. EXPORT ==========
print("10. Export du dataset nettoyé...")
output = PROCESSED_DATA_PATH
movies_final.to_csv(output, index=False)

print("\n" + "=" * 60)
print(f"✅ SUCCÈS - {movies_final.shape[0]} films traités")
print(f"📊 Colonnes: {len(final_cols)}")
print(f"💾 Fichier: {output}")
print("=" * 60)
