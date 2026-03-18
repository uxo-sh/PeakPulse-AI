import pandas as pd
import os
from datetime import datetime
import numpy as np
import ast

RAW_DIR = "../data_collector/raw"
PROCESSED_DIR = "../data_collector/processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)

print("Chargement des datasets films...")

# 1. Charger les datasets principaux
movies = pd.read_csv(f"{RAW_DIR}/movies_metadata.csv", low_memory=False)
keywords = pd.read_csv(f"{RAW_DIR}/keywords.csv")
ratings = pd.read_csv(f"{RAW_DIR}/ratings.csv")

# Nettoyer movies_metadata : supprimer lignes invalides
movies = movies[movies['id'].str.isnumeric() if 'id' in movies.columns else True]
movies['id'] = pd.to_numeric(movies['id'], errors='coerce')
movies = movies.dropna(subset=['id'])
movies['id'] = movies['id'].astype(int)

# 2. Merger avec keywords
keywords['id'] = pd.to_numeric(keywords['id'], errors='coerce')
keywords = keywords.dropna(subset=['id'])
keywords['id'] = keywords['id'].astype(int)

# Parser keywords (liste JSON)
def parse_keywords(kw_str):
    try:
        kw_list = ast.literal_eval(kw_str)
        return [item['name'] for item in kw_list] if isinstance(kw_list, list) else []
    except:
        return []

keywords['keywords_list'] = keywords['keywords'].apply(parse_keywords)
keywords_group = keywords.groupby('id')['keywords_list'].apply(lambda x: list(set(sum(x, [])))).reset_index()
keywords_group.rename(columns={'keywords_list': 'all_keywords'}, inplace=True)

movies = movies.merge(keywords_group, on='id', how='left')

# 3. Merger avec ratings pour métriques
ratings['movieId'] = pd.to_numeric(ratings['movieId'], errors='coerce')
ratings = ratings.dropna(subset=['movieId'])
ratings['movieId'] = ratings['movieId'].astype(int)

ratings_agg = ratings.groupby('movieId').agg({
    'rating': ['mean', 'count'],
    'userId': 'nunique'
}).reset_index()
ratings_agg.columns = ['movieId', 'avg_user_rating', 'num_ratings', 'num_unique_users']

# Merger via links.csv pour lier movieId à tmdbId
links = pd.read_csv(f"{RAW_DIR}/links.csv")
links['tmdbId'] = pd.to_numeric(links['tmdbId'], errors='coerce')
links = links.dropna(subset=['tmdbId'])
links['tmdbId'] = links['tmdbId'].astype(int)

ratings_agg = ratings_agg.merge(links[['movieId', 'tmdbId']], on='movieId', how='left')
ratings_agg = ratings_agg.dropna(subset=['tmdbId'])
ratings_agg['tmdbId'] = ratings_agg['tmdbId'].astype(int)

movies = movies.merge(ratings_agg[['tmdbId', 'avg_user_rating', 'num_ratings', 'num_unique_users']], left_on='id', right_on='tmdbId', how='left')

# 4. Nettoyer et parser genres
def parse_genres(genre_str):
    try:
        genre_list = ast.literal_eval(genre_str)
        return [item['name'] for item in genre_list] if isinstance(genre_list, list) else []
    except:
        return []

movies['genres_list'] = movies['genres'].apply(parse_genres)

# Genres populaires pour flags
popular_genres = ["Drama", "Comedy", "Action", "Adventure", "Thriller", "Romance", "Horror", "Science Fiction", "Crime", "Animation", "Fantasy", "Mystery", "Family", "Documentary"]

for genre in popular_genres:
    movies[f'has_{genre.lower().replace(" ", "_")}'] = movies['genres_list'].apply(lambda x: genre in x if isinstance(x, list) else False)

# 5. Calculer features supplémentaires
movies['release_date'] = pd.to_datetime(movies['release_date'], errors='coerce')
movies['days_since_release'] = (datetime.now() - movies['release_date']).dt.days

movies['budget'] = pd.to_numeric(movies['budget'], errors='coerce').fillna(0)
movies['revenue'] = pd.to_numeric(movies['revenue'], errors='coerce').fillna(0)
movies['runtime'] = pd.to_numeric(movies['runtime'], errors='coerce')

movies['popularity'] = pd.to_numeric(movies['popularity'], errors='coerce').fillna(0)
movies['vote_average'] = pd.to_numeric(movies['vote_average'], errors='coerce').fillna(0)
movies['vote_count'] = pd.to_numeric(movies['vote_count'], errors='coerce').fillna(0)

# Log transformations
movies['log_popularity'] = np.log1p(movies['popularity'])
movies['log_budget'] = np.log1p(movies['budget'])
movies['log_revenue'] = np.log1p(movies['revenue'])
movies['log_vote_count'] = np.log1p(movies['vote_count'])

# Features hybrides
movies['is_blockbuster'] = (movies['budget'] > 10000000) & (movies['revenue'] > 100000000)
movies['high_rated'] = movies['vote_average'] > 7.0
movies['cult_classic'] = (movies['vote_average'] > 6.5) & (movies['vote_count'] < 1000)

# Keywords features
def count_keywords(kw_list):
    return len(kw_list) if isinstance(kw_list, list) else 0

movies['num_keywords'] = movies['all_keywords'].apply(count_keywords)

# 6. FEATURES DE RENTABILITÉ ET ROI
movies['profit'] = movies['revenue'] - movies['budget']
movies['roi'] = np.where(
    movies['budget'] > 0,
    (movies['revenue'] - movies['budget']) / movies['budget'],
    0
)
movies['profit_ratio'] = np.where(
    movies['revenue'] > 0,
    movies['profit'] / movies['revenue'],
    0
)
movies['is_profitable'] = (movies['revenue'] > movies['budget']).astype(int)
movies['is_high_roi'] = (movies['roi'] > 2.0).astype(int)  # Retour > 100%

# 7. FEATURES COMPOSITES DE QUALITÉ
# Normaliser avg_user_rating (0-5) à l'échelle 0-10 pour comparaison avec vote_average
movies['avg_user_rating_normalized'] = movies['avg_user_rating'].fillna(5) * 2  # 5/5 -> 10/10
movies['quality_score'] = (
    movies['vote_average'] * 0.6 + 
    movies['avg_user_rating_normalized'] * 0.4
)
movies['critic_audience_gap'] = np.abs(movies['vote_average'] - movies['avg_user_rating_normalized'])

# High engagement : top 25% en nombre total de ratings
engagement_threshold = movies['num_ratings'].quantile(0.75)
movies['high_engagement'] = (movies['num_ratings'] > engagement_threshold).astype(int)

# 8. FEATURES DE HYPE ET MOMENTUM
movies['is_hotly_anticipated'] = ((movies['budget'] > 50000000) & (movies['vote_count'] < 5000)).astype(int)
movies['early_success_ratio'] = movies['vote_count'] / (movies['days_since_release'] + 1)
movies['hype_score'] = movies['popularity'] * (1 + movies['vote_average'] / 10)

# 9. FEATURES DE DIVERSITÉ CRÉATIVE
def count_genres(genre_list):
    return len(genre_list) if isinstance(genre_list, list) else 0

movies['num_genres'] = movies['genres_list'].apply(count_genres)
movies['genre_diversity_flag'] = (movies['num_genres'] > 2).astype(int)

# Crossover : combos inhabituelles (ex: comedy + horror, action + romance)
comedyhorror = movies['has_comedy'] & movies['has_horror']
actionromance = movies['has_action'] & movies['has_romance']
scifi_thriller = movies['has_science_fiction'] & movies['has_thriller']
movies['is_crossover_genre'] = (comedyhorror | actionromance | scifi_thriller).astype(int)

# 10. FEATURES D'AUDIENCE CIBLE
movies['family_friendly'] = (
    movies['has_family'] | movies['has_animation'] | 
    (movies['has_comedy'] & ~movies['has_horror'])
).astype(int)

movies['adult_focused'] = (
    movies['has_crime'] | movies['has_thriller'] | 
    (movies['has_horror'] & (movies['vote_count'] > movies['vote_count'].median()))
).astype(int)

niche_threshold = movies['vote_count'].median()
movies['niche_appeal'] = (
    movies['cult_classic'] | 
    ((movies['num_keywords'] > 10) & (movies['vote_count'] < niche_threshold))
).astype(int)

# 11. FEATURES D'ÉQUILIBRE PRODUCTION
movies['budget_runtime_ratio'] = np.where(
    movies['runtime'] > 0,
    movies['budget'] / movies['runtime'],
    0
)
movies['is_efficient'] = ((movies['revenue'] / (movies['budget'] + 1)) > 3.0).astype(int)
movies['boxoffice_per_minute'] = np.where(
    movies['runtime'] > 0,
    movies['revenue'] / movies['runtime'],
    0
)

# 12. Calculer target : trend_score_movies (améliora avec nouvelles features)
movies['trend_score_movies'] = (
    0.35 * (movies['popularity'] / (movies['popularity'].max() + 1e-10)) +
    0.25 * (movies['vote_average'] / 10) +
    0.15 * (movies['num_ratings'] / (movies['num_ratings'].max() + 1e-10)) +
    0.10 * movies['is_profitable'] +
    0.10 * (1 / (movies['days_since_release'] / 365 + 1)) +
    0.05 * (movies['quality_score'] / 10)
).clip(0, 1)  # Limiter à [0, 1]

# 13. Sélectionner colonnes finales (excluant avg_user_rating_normalized qui est intermédiaire)
final_cols = [
    'id', 'title', 'release_date', 'budget', 'revenue', 'runtime', 'popularity', 'vote_average', 'vote_count',
    'days_since_release', 'trend_score_movies', 'avg_user_rating', 'num_ratings', 'num_unique_users',
    'num_keywords', 'num_genres',
    'log_popularity', 'log_budget', 'log_revenue', 'log_vote_count',
    'profit', 'roi', 'profit_ratio', 'is_profitable', 'is_high_roi',
    'quality_score', 'critic_audience_gap', 'high_engagement',
    'is_hotly_anticipated', 'early_success_ratio', 'hype_score',
    'genre_diversity_flag', 'is_crossover_genre',
    'family_friendly', 'adult_focused', 'niche_appeal',
    'budget_runtime_ratio', 'is_efficient', 'boxoffice_per_minute',
    'is_blockbuster', 'high_rated', 'cult_classic'
] + [f'has_{g.lower().replace(" ", "_")}' for g in popular_genres]

movies_final = movies[final_cols].dropna(subset=['title', 'release_date'])

# 14. Exporter
output = f"{PROCESSED_DIR}/movies_cleaned_for_ml_{datetime.now():%Y%m%d}.csv"
movies_final.to_csv(output, index=False)

print(f"✅ Films rassemblés : {movies_final.shape[0]} lignes")
print("Colonnes ajoutées :", [c for c in movies_final.columns if c not in ['id', 'title', 'release_date', 'budget', 'revenue', 'runtime', 'popularity', 'vote_average', 'vote_count']])